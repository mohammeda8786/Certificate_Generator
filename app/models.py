from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CertificateJob(SQLModel, table=True):
    __tablename__ = "certificate_jobs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str
    issuer_name: str
    event_name: str
    issued_on: str
    status: str = "processing"
    total_recipients: int = 0
    successful_count: int = 0
    failed_count: int = 0
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class CertificateRecord(SQLModel, table=True):
    __tablename__ = "certificate_records"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="certificate_jobs.id", index=True)
    recipient_id: str
    full_name: str
    email: str
    course_name: str = ""
    score: Optional[str] = None
    organization: Optional[str] = None
    status: str = "pending"
    file_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
