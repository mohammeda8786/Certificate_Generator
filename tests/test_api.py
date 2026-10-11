from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_REQUEST = {
    "title": "Certificate of Completion",
    "issuer_name": "Acme Learning",
    "event_name": "Future Skills Bootcamp",
    "issued_on": "2026-10-11",
    "recipients": [
        {
            "recipient_id": "alice-001",
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
            "course_name": "Python Fundamentals",
            "score": "A+",
            "organization": "Acme Corp",
        },
        {
            "recipient_id": "bob-002",
            "full_name": "Bob Smith",
            "email": "bob@example.com",
            "course_name": "Cloud Essentials",
            "score": "A",
            "organization": "Northwind",
        },
    ],
}


def test_create_generation_job() -> None:
    response = client.post("/api/v1/jobs", json=VALID_REQUEST)

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["total_recipients"] == 2
    assert payload["successful_count"] == 2
    assert payload["failed_count"] == 0
    assert payload["progress_percentage"] == 100


def test_input_validation_and_partial_failure() -> None:
    request = {
        "title": "Certificate of Completion",
        "issuer_name": "Acme Learning",
        "event_name": "AI Bootcamp",
        "issued_on": "2026-10-12",
        "recipients": [
            {
                "recipient_id": "bad-001",
                "full_name": "",
                "email": "not-an-email",
                "course_name": "Intro to AI",
            },
            {
                "recipient_id": "good-001",
                "full_name": "Charlie Brown",
                "email": "charlie@example.com",
                "course_name": "Intro to AI",
            },
        ],
    }

    response = client.post("/api/v1/jobs", json=request)

    assert response.status_code == 201
    payload = response.json()
    assert payload["total_recipients"] == 2
    assert payload["successful_count"] == 1
    assert payload["failed_count"] == 1


def test_job_status_and_progress() -> None:
    response = client.post("/api/v1/jobs", json=VALID_REQUEST)
    job_id = response.json()["job_id"]

    status_response = client.get(f"/api/v1/jobs/{job_id}")
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["progress_percentage"] == 100
    assert len(data["certificates"]) == 2


def test_retrieving_generated_certificates() -> None:
    response = client.post("/api/v1/jobs", json=VALID_REQUEST)
    job_id = response.json()["job_id"]

    certs_response = client.get(f"/api/v1/jobs/{job_id}/certificates")
    assert certs_response.status_code == 200
    certs = certs_response.json()
    assert len(certs) == 2
    certificate_id = certs[0]["certificate_id"]

    file_response = client.get(f"/api/v1/certificates/{certificate_id}")
    assert file_response.status_code == 200
    assert file_response.headers["content-type"].startswith("application/pdf")
    assert len(file_response.content) > 1000


def test_individual_certificate_failure_does_not_block_valid_ones() -> None:
    request = {
        "title": "Event Attendance",
        "issuer_name": "Training Center",
        "event_name": "Data Clinic",
        "issued_on": "2026-10-13",
        "recipients": [
            {
                "recipient_id": "valid-01",
                "full_name": "Diana Ross",
                "email": "diana@example.com",
                "course_name": "Analytics",
            },
            {
                "recipient_id": "fail-01",
                "full_name": "", 
                "email": "broken@example.com",
                "course_name": "Analytics",
            },
        ],
    }

    response = client.post("/api/v1/jobs", json=request)
    assert response.status_code == 201
    data = response.json()
    assert data["successful_count"] == 1
    assert data["failed_count"] == 1

    certs = client.get(f"/api/v1/jobs/{data['job_id']}/certificates").json()
    assert len(certs) == 2
    statuses = {item["status"] for item in certs}
    assert statuses == {"success", "failed"}
