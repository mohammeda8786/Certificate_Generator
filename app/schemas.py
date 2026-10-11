from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RecipientInput(BaseModel):
    recipient_id: str = Field(..., min_length=1)
    full_name: str = ""
    email: str = ""
    course_name: str = ""
    score: Optional[str] = None
    organization: Optional[str] = None


class CertificateGenerationRequest(BaseModel):
    title: str = Field(..., min_length=1)
    issuer_name: str = Field(..., min_length=1)
    event_name: str = Field(..., min_length=1)
    issued_on: str = Field(..., min_length=1)
    recipients: list[RecipientInput] = Field(..., min_length=1)


class JobSummary(BaseModel):
    job_id: str
    title: str
    issuer_name: str
    event_name: str
    issued_on: str
    status: str
    total_recipients: int
    successful_count: int
    failed_count: int
    progress_percentage: int


class CertificateSummary(BaseModel):
    certificate_id: str
    job_id: str
    recipient_id: str
    full_name: str
    email: str
    course_name: str
    score: Optional[str] = None
    organization: Optional[str] = None
    status: str
    file_path: Optional[str] = None
    error_message: Optional[str] = None


class JobDetail(JobSummary):
    certificates: list[CertificateSummary]
