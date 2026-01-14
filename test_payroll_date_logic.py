import unittest
from datetime import datetime

# Logic extracted from the endpoint for testing purposes
def get_payroll_dates(month=None, year=None, current_date=None):
    if current_date is None:
        current_date = datetime.now()
    
    if month is not None and year is not None:
        target_month = month
        target_year = year
    else:
        # Auto-detect based on current_date
        if current_date.day >= 26:
            if current_date.month == 12:
                target_month = 1
                target_year = current_date.year + 1
            else:
                target_month = current_date.month + 1
                target_year = current_date.year
        else:
            target_month = current_date.month
            target_year = current_date.year

    if target_month == 1:
        prev_month = 12
        prev_month_year = target_year - 1
    else:
        prev_month = target_month - 1
        prev_month_year = target_year

    start_dt = datetime(prev_month_year, prev_month, 26)
    end_dt = datetime(target_year, target_month, 25)
    
    return start_dt, end_dt, target_year, target_month

class TestPayrollDates(unittest.TestCase):
    def test_explicit_month_feb(self):
        # Target: Feb 2024 -> Jan 26, 2024 to Feb 25, 2024
        start, end, _, _ = get_payroll_dates(month=2, year=2024)
        self.assertEqual(start, datetime(2024, 1, 26))
        self.assertEqual(end, datetime(2024, 2, 25))

    def test_explicit_month_jan(self):
        # Target: Jan 2024 -> Dec 26, 2023 to Jan 25, 2024
        start, end, _, _ = get_payroll_dates(month=1, year=2024)
        self.assertEqual(start, datetime(2023, 12, 26))
        self.assertEqual(end, datetime(2024, 1, 25))

    def test_auto_detect_early_jan(self):
        # Today: Jan 10, 2024 -> Target Jan 2024 (Dec 26 - Jan 25)
        today = datetime(2024, 1, 10)
        start, end, ty, tm = get_payroll_dates(current_date=today)
        self.assertEqual(ty, 2024)
        self.assertEqual(tm, 1)
        self.assertEqual(start, datetime(2023, 12, 26))
        self.assertEqual(end, datetime(2024, 1, 25))

    def test_auto_detect_late_jan(self):
        # Today: Jan 26, 2024 -> Target Feb 2024 (Jan 26 - Feb 25)
        today = datetime(2024, 1, 26)
        start, end, ty, tm = get_payroll_dates(current_date=today)
        self.assertEqual(ty, 2024)
        self.assertEqual(tm, 2)
        self.assertEqual(start, datetime(2024, 1, 26))
        self.assertEqual(end, datetime(2024, 2, 25))

    def test_auto_detect_late_dec(self):
        # Today: Dec 27, 2023 -> Target Jan 2024 (Dec 26 - Jan 25)
        today = datetime(2023, 12, 27)
        start, end, ty, tm = get_payroll_dates(current_date=today)
        self.assertEqual(ty, 2024)
        self.assertEqual(tm, 1)
        self.assertEqual(start, datetime(2023, 12, 26))
        self.assertEqual(end, datetime(2024, 1, 25))

if __name__ == '__main__':
    unittest.main()
