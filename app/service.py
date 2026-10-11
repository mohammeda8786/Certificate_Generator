from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException
from fastapi.responses import FileResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlmodel import Session, select

from .models import CertificateJob, CertificateRecord
from .schemas import CertificateGenerationRequest, CertificateSummary, JobDetail, JobSummary

ROOT_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = ROOT_DIR / "storage" / "certificates"


def _validate_recipient(recipient: CertificateRecord) -> None:
    if not recipient.full_name.strip():
        raise ValueError("full_name is required")
    if not recipient.email.strip():
        raise ValueError("email is required")
    if "@" not in recipient.email or "." not in recipient.email.split("@")[-1]:
        raise ValueError("email is invalid")


def _build_file_path(job_id: str, record_id: str) -> str:
    relative_path = Path("storage") / "certificates" / job_id / f"{record_id}.pdf"
    return relative_path.as_posix()


def _generate_certificate_pdf(job: CertificateJob, record: CertificateRecord) -> str:
    job_dir = STORAGE_DIR / job.id
    job_dir.mkdir(parents=True, exist_ok=True)
    file_path = job_dir / f"{record.id}.pdf"

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(job.title, styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Issued by <b>{job.issuer_name}</b>", styles["BodyText"]))
    story.append(Paragraph(f"Event: <b>{job.event_name}</b>", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph(f"This certificate is awarded to <b>{record.full_name}</b>", styles["BodyText"]))
    story.append(Paragraph(f"for successful completion of <b>{record.course_name or 'Completion Program'}</b>", styles["BodyText"]))
    if record.organization:
        story.append(Paragraph(f"Organization: <b>{record.organization}</b>", styles["BodyText"]))
    if record.score:
        story.append(Paragraph(f"Score: <b>{record.score}</b>", styles["BodyText"]))
    story.append(Spacer(1, 18))
    story.append(Paragraph(f"Issued on: <b>{job.issued_on}</b>", styles["BodyText"]))

    document = SimpleDocTemplate(str(file_path), pagesize=A4)
    document.build(story)
    return _build_file_path(job.id, record.id)


def serialize_certificate(record: CertificateRecord) -> CertificateSummary:
    return CertificateSummary(
        certificate_id=record.id,
        job_id=record.job_id,
        recipient_id=record.recipient_id,
        full_name=record.full_name,
        email=record.email,
        course_name=record.course_name,
        score=record.score,
        organization=record.organization,
        status=record.status,
        file_path=record.file_path,
        error_message=record.error_message,
    )


def build_job_summary(job: CertificateJob, certificates: list[CertificateRecord]) -> JobSummary:
    if job.total_recipients == 0:
        progress_percentage = 0
    else:
        progress_percentage = int((job.successful_count + job.failed_count) / job.total_recipients * 100)

    return JobSummary(
        job_id=job.id,
        title=job.title,
        issuer_name=job.issuer_name,
        event_name=job.event_name,
        issued_on=job.issued_on,
        status=job.status,
        total_recipients=job.total_recipients,
        successful_count=job.successful_count,
        failed_count=job.failed_count,
        progress_percentage=progress_percentage,
    )


def build_job_detail(job: CertificateJob, certificates: list[CertificateRecord]) -> JobDetail:
    summary = build_job_summary(job, certificates)
    return JobDetail(**summary.model_dump(), certificates=[serialize_certificate(item) for item in certificates])


def create_job_and_generate_certificates(payload: CertificateGenerationRequest, session: Session) -> CertificateJob:
    job = CertificateJob(
        title=payload.title,
        issuer_name=payload.issuer_name,
        event_name=payload.event_name,
        issued_on=payload.issued_on,
        total_recipients=len(payload.recipients),
        status="processing",
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    certificates: list[CertificateRecord] = []
    for recipient in payload.recipients:
        record = CertificateRecord(
            job_id=job.id,
            recipient_id=recipient.recipient_id,
            full_name=recipient.full_name.strip(),
            email=recipient.email.strip(),
            course_name=(recipient.course_name or "").strip(),
            score=(recipient.score or "").strip() or None,
            organization=(recipient.organization or "").strip() or None,
        )
        certificates.append(record)
        session.add(record)

    session.commit()

    for record in certificates:
        try:
            _validate_recipient(record)
            record.file_path = _generate_certificate_pdf(job, record)
            record.status = "success"
            job.successful_count += 1
        except Exception as exc:  # noqa: BLE001 - preserve job-level failure handling
            record.status = "failed"
            record.error_message = str(exc)
            record.file_path = None
            job.failed_count += 1
        finally:
            record.updated_at = datetime.now(timezone.utc)
            session.add(record)
            session.commit()

    job.status = "completed"
    job.updated_at = datetime.now(timezone.utc)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job_or_404(job_id: str, session: Session) -> CertificateJob:
    job = session.get(CertificateJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def get_certificate_or_404(certificate_id: str, session: Session) -> CertificateRecord:
    record = session.get(CertificateRecord, certificate_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return record


def fetch_job_detail(job_id: str, session: Session) -> JobDetail:
    job = get_job_or_404(job_id, session)
    records = session.exec(select(CertificateRecord).where(CertificateRecord.job_id == job_id)).all()
    return build_job_detail(job, records)


def fetch_certificate_list(job_id: str, session: Session) -> list[CertificateSummary]:
    get_job_or_404(job_id, session)
    records = session.exec(select(CertificateRecord).where(CertificateRecord.job_id == job_id)).all()
    return [serialize_certificate(record) for record in records]


def fetch_certificate_file(certificate_id: str, session: Session) -> FileResponse:
    record = get_certificate_or_404(certificate_id, session)
    if not record.file_path:
        raise HTTPException(status_code=404, detail="This certificate was not generated successfully")

    file_path = (ROOT_DIR / record.file_path).resolve()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Certificate file not found")

    return FileResponse(path=file_path, media_type="application/pdf", filename=f"certificate_{record.id}.pdf")
