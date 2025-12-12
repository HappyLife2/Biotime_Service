# BioTime Attendance Service

A robust FastAPI-based service to interact with BioTime (biometrics) software, generating attendance reports and summaries.

## Features

- **Employee List**: Fetch all employees from BioTime.
- **Attendance Transactions**: Retrieve raw punch logs.
- **Daily Summaries**:
    - `GET /attendance/today` - Summary of today's attendance per employee.
    - `GET /attendance/today/late` - List of employees late today.
    - `GET /attendance/today/absent` - List of employees absent today.
- **Reporting**:
    - **Live Monthly Report**: `GET /attendance/report/monthly` (Defaults to current month-to-date). Supports `?month=X&year=Y` filtering.
    - **Live Weekly Report**: `GET /attendance/report/weekly` (Defaults to current week-to-date).
    - **Previous Month**: `GET /attendance/report/monthly-previous` (Full completed previous month).

## Configuration

The service uses environment variables for configuration, with sensible defaults:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `BIOTIME_BASE` | `http://192.168.15.114` | Base URL of the BioTime server |
| `BIOTIME_USERNAME` | `HR` | Admin username |
| `BIOTIME_PASSWORD` | `2025@qazxsw` | Admin password |
| `WORK_START_TIME` | `08:00:00` | Official work start time |
| `LATE_AFTER_TIME` | `08:05:00` | Time after which an employee is marked late |
| `EARLY_LEAVE_TIME` | `17:00:00` | Time before which departure is "early" |

## Business Logic

- **Working Days**: Monday through Saturday.
- **Weekends**: Sunday (Attendance on Sunday is counted as present, but Sunday absence doesn't count against required days).

## Setup & Running

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Server**:
    ```bash
    python biotime_service.py
    # or
    uvicorn biotime_service:app --reload
    ```
    Server runs on `http://0.0.0.0:8000`.

## Documentation

See [WALKTHROUGH.md](WALKTHROUGH.md) for detailed verification steps and recent changes.
