# Bulk Certificate Generator Backend

This project implements a backend API for creating bulk certificate-generation jobs for event participants. It accepts a list of recipients, validates each entry, generates a certificate PDF for each valid recipient, and exposes endpoints to track job progress and download the generated certificates.

## Stack

- Python 3.12+
- FastAPI
- SQLModel + SQLite
- ReportLab for PDF generation
- pytest for automated tests

## Project structure

- `app/main.py` – FastAPI application and endpoints
- `app/service.py` – certificate generation and validation logic
- `app/models.py` – database models for jobs and certificate records
- `app/schemas.py` – API request/response contracts
- `app/database.py` – database engine and session setup
- `tests/test_api.py` – endpoint and behavior tests
- `storage/certificates/` – generated PDF files

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   . .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the API:

   ```bash
   uvicorn app.main:app --reload
   ```

The app will run on `http://127.0.0.1:8000` by default.

## API usage

### Create a certificate generation job

POST `/api/v1/jobs`

Example JSON payload:

```json
{
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
      "organization": "Acme Corp"
    },
    {
      "recipient_id": "bob-002",
      "full_name": "Bob Smith",
      "email": "bob@example.com",
      "course_name": "Cloud Essentials",
      "score": "A"
    }
  ]
}
```

The API validates each recipient. Invalid entries are tracked as failed while valid recipients still generate certificates.

### Check job status

GET `/api/v1/jobs/{job_id}`

This returns:

- the overall job status
- the total recipient count
- successful and failed counts
- the progress percentage
- per-recipient result details

### Retrieve generated certificates

GET `/api/v1/jobs/{job_id}/certificates`

or download one certificate directly:

GET `/api/v1/certificates/{certificate_id}`

## Design decisions

- I used a single predefined PDF template so the system can generate bulk certificates without a full template editor.
- I chose synchronous generation for this assessment because it keeps the application simple, reliable, and easy to explain during an interview. The API still accepts a batch of recipients and tracks each recipient result individually.
- SQLite is used to satisfy the relational database requirement without requiring external infrastructure.

## Running tests

```bash
pytest -q
```

## Notes

The generated certificates are stored under `storage/certificates/<job_id>/` so they can be retrieved after creation.
