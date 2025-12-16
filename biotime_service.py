# biotime_service.py
import os
import requests
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import uvicorn

# ----------- CONFIG / ENV VARS -----------
# Pull from env, but fall back to defaults
_raw_base = os.environ.get("BIOTIME_BASE") or "http://localhost:8080"

# Ensure it always has a scheme
if not _raw_base.startswith("http://") and not _raw_base.startswith("https://"):
    _raw_base = "http://" + _raw_base

BIOTIME_BASE = _raw_base.rstrip("/")  # remove trailing slash just in case

USERNAME = os.environ.get("BIOTIME_USERNAME") or "admin"
PASSWORD = os.environ.get("BIOTIME_PASSWORD") or "password"

# ---- Attendance rules (adjust as needed) ----
WORK_START_TIME = os.environ.get("WORK_START_TIME") or "08:00:00"       # Official start time
LATE_AFTER_TIME = os.environ.get("LATE_AFTER_TIME") or "08:05:00"       # After this = late
EARLY_LEAVE_TIME = os.environ.get("EARLY_LEAVE_TIME") or "17:00:00"     # Before this = early leave

app = FastAPI()

print("=== Biotime config at startup ===")
print(f"BIOTIME_BASE     = {BIOTIME_BASE}")
print(f"USERNAME         = {USERNAME}")
print(f"WORK_START_TIME  = {WORK_START_TIME}")
print(f"LATE_AFTER_TIME  = {LATE_AFTER_TIME}")
print(f"EARLY_LEAVE_TIME = {EARLY_LEAVE_TIME}")
print("=================================")


# ----------------------------------------------------
# HELPER FUNCTIONS
# ----------------------------------------------------
def get_token():
    url = f"{BIOTIME_BASE}/jwt-api-token-auth/"
    resp = requests.post(
        url,
        json={
            "username": USERNAME,
            "password": PASSWORD,
        },
        timeout=10,
    )

    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()["token"]


def fetch_employees(page: int = 1, page_size: int = 1000):
    """
    Fetch employees from Biotime (single page).
    For production you may want to loop over pages if you have many employees.
    """
    token = get_token()
    url = f"{BIOTIME_BASE}/personnel/api/employees/"

    resp = requests.get(
        url,
        headers={"Authorization": f"JWT {token}"},
        params={"page": page, "page_size": page_size},
        timeout=15,
    )

    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


def fetch_transactions(
    emp_code: str = None,
    start_time: str = None,
    end_time: str = None,
    page: int = 1,
    page_size: int = 1000,
):
    """
    Fetch transactions (punch logs) from Biotime.
    """
    token = get_token()
    url = f"{BIOTIME_BASE}/iclock/api/transactions/"

    params = {
        "page": page,
        "page_size": page_size,
    }

    if emp_code:
        params["emp_code"] = emp_code
    if start_time:
        params["start_time"] = start_time
    if end_time:
        params["end_time"] = end_time

    resp = requests.get(
        url,
        headers={"Authorization": f"JWT {token}"},
        params=params,
        timeout=30,
    )

    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


def build_attendance_summary(start_dt: datetime, end_dt: datetime):
    """
    Build attendance summary for a given date range (inclusive) per employee.
    Returns:
        {
          "start_date": "...",
          "end_date": "...",
          "data": [
             {
               "emp_code": "...",
               "first_name": "...",
               "department": "...",
               "first_punch_time": "...",
               "last_punch_time": "...",
               "total_punches": n,
             },
             ...
          ]
        }
    """
    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    tx_resp = fetch_transactions(
        start_time=start_str,
        end_time=end_str,
        page=1,
        page_size=2000,  # adjust if needed
    )
    records = tx_resp.get("data", [])

    grouped = defaultdict(list)
    for rec in records:
        grouped[rec["emp_code"]].append(rec)

    summary = []

    for emp_code, punches in grouped.items():
        punches_sorted = sorted(
            punches,
            key=lambda r: datetime.strptime(r["punch_time"], "%Y-%m-%d %H:%M:%S"),
        )
        first_punch = punches_sorted[0]
        last_punch = punches_sorted[-1]

        summary.append(
            {
                "emp_code": emp_code,
                "first_name": first_punch.get("first_name"),
                "department": first_punch.get("department"),
                "first_punch_time": first_punch.get("punch_time"),
                "first_terminal_alias": first_punch.get("terminal_alias"),
                "last_punch_time": last_punch.get("punch_time"),
                "last_terminal_alias": last_punch.get("terminal_alias"),
                "total_punches": len(punches_sorted),
            }
        )

    summary_sorted = sorted(summary, key=lambda r: r["emp_code"])

    return {
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "end_date": end_dt.strftime("%Y-%m-%d"),
        "count": len(summary_sorted),
        "data": summary_sorted,
    }


# ----------------------------------------------------
# API ENDPOINTS
# ----------------------------------------------------

# EMPLOYEES
@app.get("/employees")
def list_employees(page: int = 1, page_size: int = 100):
    return fetch_employees(page=page, page_size=page_size)


# RAW TRANSACTIONS
@app.get("/transactions")
def get_transactions(
    emp_code: str = None,
    start_time: str = None,
    end_time: str = None,
    page: int = 1,
    page_size: int = 100,
):
    return fetch_transactions(
        emp_code=emp_code,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size,
    )


# TODAY'S RAW TRANSACTIONS
@app.get("/transactions/today")
def get_todays_transactions(page: int = 1, page_size: int = 500):
    today = datetime.now().strftime("%Y-%m-%d")
    start = datetime.strptime(f"{today} 00:00:00", "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(f"{today} 23:59:59", "%Y-%m-%d %H:%M:%S")

    return fetch_transactions(
        start_time=start.strftime("%Y-%m-%d %H:%M:%S"),
        end_time=end.strftime("%Y-%m-%d %H:%M:%S"),
        page=page,
        page_size=page_size,
    )


# TODAY'S ATTENDANCE SUMMARY (PER EMPLOYEE)
@app.get("/attendance/today")
def attendance_today():
    today = datetime.now().strftime("%Y-%m-%d")
    start_dt = datetime.strptime(f"{today} 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(f"{today} 23:59:59", "%Y-%m-%d %H:%M:%S")

    summary = build_attendance_summary(start_dt, end_dt)
    # keep "date" for convenience
    summary["date"] = today
    return summary


# PRESENT TODAY (employees who have at least one punch)
@app.get("/attendance/today/present")
def attendance_today_present():
    today_summary = attendance_today()
    return {
        "date": today_summary["date"],
        "count": today_summary["count"],
        "data": today_summary["data"],
    }


# ABSENT TODAY (employees with no punches)
@app.get("/attendance/today/absent")
def attendance_today_absent():
    # Fetch all employees (single page, adjust if many)
    emp_resp = fetch_employees(page=1, page_size=1000)
    employees = emp_resp.get("data", [])

    # Get today's present summary
    today_summary = attendance_today()
    present_codes = {row["emp_code"] for row in today_summary["data"]}

    absent = []
    for emp in employees:
        code = emp.get("emp_code")
        # If emp_code is empty or None, skip
        if not code:
            continue
        if code not in present_codes:
            absent.append(
                {
                    "emp_code": code,
                    "first_name": emp.get("first_name"),
                    "last_name": emp.get("last_name"),
                    "department": (emp.get("department") or {}).get("dept_name")
                    if isinstance(emp.get("department"), dict)
                    else None,
                }
            )

    absent_sorted = sorted(absent, key=lambda r: r["emp_code"])

    return {
        "date": today_summary["date"],
        "count": len(absent_sorted),
        "data": absent_sorted,
    }


# LATE TODAY (first punch after LATE_AFTER_TIME)
@app.get("/attendance/today/late")
def attendance_today_late():
    today_summary = attendance_today()
    today_date = today_summary["date"]

    late_threshold = datetime.strptime(
        f"{today_date} {LATE_AFTER_TIME}", "%Y-%m-%d %H:%M:%S"
    )

    late_list = []
    for row in today_summary["data"]:
        fp = datetime.strptime(row["first_punch_time"], "%Y-%m-%d %H:%M:%S")
        if fp > late_threshold:
            late_list.append(row)

    return {
        "date": today_date,
        "count": len(late_list),
        "data": late_list,
        "late_after_time": LATE_AFTER_TIME,
    }


# EARLY LEAVE TODAY (last punch before EARLY_LEAVE_TIME)
@app.get("/attendance/today/early-leave")
def attendance_today_early_leave():
    today_summary = attendance_today()
    today_date = today_summary["date"]

    early_threshold = datetime.strptime(
        f"{today_date} {EARLY_LEAVE_TIME}", "%Y-%m-%d %H:%M:%S"
    )

    early_list = []
    for row in today_summary["data"]:
        lp = datetime.strptime(row["last_punch_time"], "%Y-%m-%d %H:%M:%S")
        if lp < early_threshold:
            early_list.append(row)

    return {
        "date": today_date,
        "count": len(early_list),
        "data": early_list,
        "early_leave_before": EARLY_LEAVE_TIME,
    }


# WEEKLY ATTENDANCE SUMMARY (LAST 7 DAYS)
@app.get("/attendance/week")
def attendance_week():
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=6)  # last 7 days including today
    summary = build_attendance_summary(start_dt, end_dt)
    summary["period"] = "last_7_days"
    return summary


# MONTHLY ATTENDANCE SUMMARY (CURRENT MONTH TO DATE)
@app.get("/attendance/month")
def attendance_month():
    now = datetime.now()
    start_dt = datetime(now.year, now.month, 1)
    end_dt = now
    summary = build_attendance_summary(start_dt, end_dt)
    summary["period"] = "month_to_date"
    return summary


# ----------------------------------------------------
# MONTHLY REPORT (STATS)
# ----------------------------------------------------
def fetch_all_employees():
    """
    Fetch ALL employees by looping through pages.
    """
    all_employees = []
    page = 1
    while True:
        resp = fetch_employees(page=page, page_size=1000)
        data = resp.get("data", [])
        if not data:
            break
        all_employees.extend(data)
        
        # Check if we have more pages
        # The API response usually mimics Django Rest Framework pagination
        # "next": "http://.../?page=2" or None
        if not resp.get("next"):
            break
        page += 1
    return all_employees


def fetch_all_transactions(start_time: str, end_time: str):
    """
    Fetch ALL transactions for the given period by looping through pages.
    """
    all_tx = []
    page = 1
    while True:
        resp = fetch_transactions(
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=2000
        )
        data = resp.get("data", [])
        if not data:
            break
        all_tx.extend(data)
        
        if not resp.get("next"):
            break
        page += 1
    return all_tx


def calculate_attendance_stats(start_dt: datetime, end_dt: datetime):
    """
    Core logic to fetch data and calculate attendance stats for a date range.
    Returns sorted list of dicts with employee stats.
    """
    start_str = start_dt.strftime("%Y-%m-%d %H:%M:%S")
    end_str = end_dt.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Fetch Data
    employees = fetch_all_employees()
    transactions = fetch_all_transactions(start_str, end_str)

    # 2. Index Transactions: punches_map[emp_code][date_str] = [punch_obj... ]
    punches_map = defaultdict(lambda: defaultdict(list))
    for tx in transactions:
        emp_code = tx.get("emp_code")
        p_time = tx.get("punch_time")
        if not emp_code or not p_time:
            continue
        date_str = p_time.split(" ")[0]
        punches_map[emp_code][date_str].append(tx)

    # 3. Time Thresholds
    late_time_struct = datetime.strptime(LATE_AFTER_TIME, "%H:%M:%S").time()

    # 4. Generate Date List
    all_dates = []
    curr = start_dt
    while curr.date() <= end_dt.date():
        all_dates.append(curr)
        curr += timedelta(days=1)

    # 5. Calculate per Employee
    report_data = []

    for emp in employees:
        code = emp.get("emp_code")
        if not code:
            continue
            
        first_name = emp.get("first_name", "")
        last_name = emp.get("last_name", "")
        # Safe access to department name
        dept = (emp.get("department") or {}).get("dept_name") if isinstance(emp.get("department"), dict) else None

        days_present = 0
        days_late = 0
        days_absent = 0
        total_required_days = 0
        
        late_details = []
        absent_details = []
        
        emp_punches = punches_map.get(code, {})

        for day in all_dates:
            d_str = day.strftime("%Y-%m-%d")
            
            # Weekend Check: User specified Mon-Sat are working days.
            # So only Sunday (6) is a weekend.
            is_weekend = day.weekday() == 6 

            daily_txs = emp_punches.get(d_str, [])
            has_punches = len(daily_txs) > 0
            
            if is_weekend:
                if has_punches:
                    days_present += 1
                continue
            
            # -- Weekdays --
            total_required_days += 1
            
            if not has_punches:
                days_absent += 1
                absent_details.append(d_str)
            else:
                days_present += 1
                
                # Check Late
                sorted_punches = sorted(daily_txs, key=lambda x: x["punch_time"])
                first_punch_str = sorted_punches[0]["punch_time"]
                first_punch_dt = datetime.strptime(first_punch_str, "%Y-%m-%d %H:%M:%S")
                
                threshold_dt = datetime.combine(day.date(), late_time_struct)
                if first_punch_dt > threshold_dt:
                    days_late += 1
                    late_details.append({
                        "date": d_str,
                        "punch_time": first_punch_str,
                        "late_by": str(first_punch_dt - threshold_dt)
                    })

        report_data.append({
            "emp_code": code,
            "first_name": first_name,
            "last_name": last_name,
            "department": dept,
            "stats": {
                "work_days_required": total_required_days,
                "present": days_present,
                "late": days_late,
                "absent": days_absent,
                "late_details": late_details,
                "absent_details": absent_details
            }
        })

    report_data.sort(key=lambda x: x["emp_code"])
    return report_data


@app.get("/attendance/report/monthly")
def attendance_report_monthly(month: int = None, year: int = None):
    """
    Monthly Report:
    - If month/year provided: Full month (1st to Last Day).
    - If missing: Current Month-to-Date (1st to Now).
    Filters: Returns only employees with late > 0 OR absent > 0.
    """
    now = datetime.now()
    
    if month and year:
        # Custom Month
        start_dt = datetime(year, month, 1)
        # Calculate end of month
        # Logic: (1st of next month) - 1 second
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        end_dt = next_month - timedelta(seconds=1)
        
        period_type = "custom_month"
    else:
        # Current Month-to-Date
        start_dt = datetime(now.year, now.month, 1)
        end_dt = now
        period_type = "current_month_to_date"

    all_data = calculate_attendance_stats(start_dt, end_dt)
    
    # Filter: Late or Absent only
    filtered_data = [
        d for d in all_data 
        if d["stats"]["late"] > 0 or d["stats"]["absent"] > 0
    ]

    return {
        "period": period_type,
        "period_start": start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "period_end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(filtered_data),
        "data": filtered_data
    }


@app.get("/attendance/report/weekly")
def attendance_report_weekly():
    """
    Weekly Report:
    - Defaults to Current Week-to-Date (Monday to Now).
    Filters: Returns only employees with late > 0 OR absent > 0.
    """
    now = datetime.now()
    # Find this week's Monday
    days_since_monday = now.weekday()  # Mon=0, Sun=6
    this_monday = now - timedelta(days=days_since_monday)
    this_monday = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # End is NOW (Live)
    end_dt = now

    all_data = calculate_attendance_stats(this_monday, end_dt)
    
    # Filter: Late or Absent only
    filtered_data = [
        d for d in all_data 
        if d["stats"]["late"] > 0 or d["stats"]["absent"] > 0
    ]

    return {
        "period": "current_week_to_date",
        "period_start": this_monday.strftime("%Y-%m-%d %H:%M:%S"),
        "period_end": end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(filtered_data),
        "data": filtered_data
    }


@app.get("/attendance/report/monthly-previous")
def attendance_report_monthly_previous():
    """
    Report for the COMPLETED previous calendar month (1st to last day).
    Returns only employees who have late > 0 OR absent > 0.
    """
    now = datetime.now()
    # First day of this month
    this_month_first = datetime(now.year, now.month, 1)
    # Last day of previous month = this_month_first - 1 second
    prev_month_last = this_month_first - timedelta(seconds=1)
    # First day of previous month
    prev_month_first = datetime(prev_month_last.year, prev_month_last.month, 1)
    
    all_data = calculate_attendance_stats(prev_month_first, prev_month_last)
    
    # Filter: Late or Absent only
    filtered_data = [
        d for d in all_data 
        if d["stats"]["late"] > 0 or d["stats"]["absent"] > 0
    ]

    return {
        "period": "previous_month",
        "period_start": prev_month_first.strftime("%Y-%m-%d %H:%M:%S"),
        "period_end": prev_month_last.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(filtered_data),
        "data": filtered_data
    }

# ----------------------------------------------------
# RUN SERVER IF FILE IS EXECUTED DIRECTLY
# ----------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("biotime_service:app", host="0.0.0.0", port=8000, reload=False)
