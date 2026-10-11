from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from .database import get_session, init_db
from .models import CertificateRecord
from .schemas import CertificateGenerationRequest, CertificateSummary, JobDetail, JobSummary
from .service import (
    create_job_and_generate_certificates,
    fetch_certificate_file,
    fetch_certificate_list,
    fetch_job_detail,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Bulk Certificate Generator API", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/jobs", response_model=JobSummary, status_code=201)
def create_certificate_job(
    payload: CertificateGenerationRequest,
    session: Session = Depends(get_session),
) -> JobSummary:
    job = create_job_and_generate_certificates(payload, session)
    records = session.exec(select(CertificateRecord).where(CertificateRecord.job_id == job.id)).all()
    from .service import build_job_summary

    return build_job_summary(job, records)


@app.get("/api/v1/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: str, session: Session = Depends(get_session)) -> JobDetail:
    return fetch_job_detail(job_id, session)


@app.get("/api/v1/jobs/{job_id}/certificates", response_model=list[CertificateSummary])
def get_job_certificates(job_id: str, session: Session = Depends(get_session)) -> list[CertificateSummary]:
    return fetch_certificate_list(job_id, session)


@app.get("/api/v1/certificates/{certificate_id}")
def get_certificate(certificate_id: str, session: Session = Depends(get_session)) -> FileResponse:
    return fetch_certificate_file(certificate_id, session)
