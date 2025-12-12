# Walkthrough - Weekly and Monthly Attendance Reports

I have added two new endpoints to the `biotime_service.py` service to generate reports for employees who were late or absent during the previous week or month.

## Changes

### 1. Refactoring
I extracted the attendance accounting logic from the annual report endpoint into a reusable helper function `calculate_attendance_stats`. This ensures consistent calculation rules across all timeframes.

### 2. New Endpoints

#### `GET /attendance/report/weekly-previous`
- **Timeframe**: Even full usage of the *previous* week (Monday through Sunday).
- **Filter**: Only returns employees with `late > 0` or `absent > 0` during that week.
- **Use Case**: For weekly status meetings or HR review every Monday.

#### `GET /attendance/report/monthly-previous`
- **Timeframe**: The full *previous* calendar month (e.g. if today is Dec 11th, it reports on Nov 1st - Nov 30th).
- **Filter**: Only returns employees with `late > 0` or `absent > 0` during that month.
- **Use Case**: Monthly payroll or disciplinary review.

## Verification Results

### Date Logic Verification
I ran a test script to verify the date range calculations based on the current date (Dec 11, 2025).

| Report | Logic Check | Result |
| :--- | :--- | :--- |
| **Weekly** | Last full Mon-Sun block | **PASS** (2025-12-01 to 2025-12-07) |
| **Monthly** | Previous complete month | **PASS** (2025-11-01 to 2025-11-30) |

### Syntax Check
The updated service file passed Python syntax verification.

## Usage
You can now update your n8n workflow or other clients to call these new endpoints.

```bash
# Example Request for Weekly Report
curl http://localhost:8000/attendance/report/weekly-previous

# Example Request for Monthly Report
curl http://localhost:8000/attendance/report/monthly-previous
```

## Business Logic Updates
- **Working Days**: Changed to **Monday through Saturday**. Only Sunday is considered a weekend/non-working day. Saturdays now contribute to 'work_days_required' and are checked for lateness/absence.
