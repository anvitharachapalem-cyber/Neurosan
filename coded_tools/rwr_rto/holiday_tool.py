"""
RWR-RTO Holiday Tool
Manages USA federal public holidays for the RWR-RTO system.

Responsibilities:
  - Block WFH request submission on USA federal holidays
  - Count effective WFH days in a date range (calendar days minus holidays)
    for accurate quota deduction
  - List holidays for a given year

All holiday data is stored in the `usa_holidays` table in the SQLite DB.
"""
import os
import sqlite3
from datetime import date, datetime
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.rwr_rto.database_tool import initialize_database

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "rwr_rto.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def is_usa_holiday(check_date: str) -> Dict:
    """
    Check if a YYYY-MM-DD string is a USA federal holiday.
    Returns {"is_holiday": bool, "holiday_name": str|None}.
    Gracefully returns is_holiday=False if the table is not yet available.
    """
    try:
        conn = _conn()
        row = conn.execute(
            "SELECT name FROM usa_holidays WHERE holiday_date=?", (check_date,)
        ).fetchone()
        conn.close()
        if row:
            return {"is_holiday": True, "holiday_name": row["name"]}
        return {"is_holiday": False, "holiday_name": None}
    except Exception:
        return {"is_holiday": False, "holiday_name": None}


def get_holidays_in_range(start: str, end: str):
    """
    Return list of USA federal holidays in [start, end] as {date, name} dicts.
    Gracefully returns empty list if table is not yet available.
    """
    try:
        conn = _conn()
        rows = conn.execute(
            "SELECT holiday_date, name FROM usa_holidays "
            "WHERE holiday_date >= ? AND holiday_date <= ? ORDER BY holiday_date",
            (start, end),
        ).fetchall()
        conn.close()
        return [{"date": r["holiday_date"], "name": r["name"]} for r in rows]
    except Exception:
        return []


class HolidayTool(CodedTool):
    """
    CodedTool for USA federal holiday management.

    Supported operations (pass via args["operation"]):
        is_holiday            — check if a specific date is a USA federal holiday;
                                returns allowed_to_submit=False if it is
        list_holidays         — list all USA federal holidays for a given year
        count_effective_days  — count calendar days in a date range, excluding federal holidays,
                                to determine the correct WFH quota consumption
    """

    def __init__(self):
        super().__init__()
        initialize_database()

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        op = args.get("operation", "is_holiday")
        dispatch = {
            "is_holiday":           self._is_holiday,
            "list_holidays":        self._list_holidays,
            "count_effective_days": self._count_effective_days,
        }
        handler = dispatch.get(op)
        if not handler:
            return {"error": f"Unknown operation: '{op}'. Valid: {list(dispatch.keys())}"}
        return handler(args)

    # ------------------------------------------------------------------ #
    #  Operations                                                          #
    # ------------------------------------------------------------------ #

    def _is_holiday(self, args: Dict[str, Any]) -> Dict[str, Any]:
        check_date = args.get("date", datetime.now().date().isoformat())
        result = is_usa_holiday(check_date)
        if result["is_holiday"]:
            return {
                "date": check_date,
                "is_holiday": True,
                "holiday_name": result["holiday_name"],
                "allowed_to_submit": False,
                "message": (
                    f"{check_date} is a USA federal holiday: {result['holiday_name']}. "
                    "WFH requests cannot start on a federal holiday. "
                    "Please choose a different start date."
                ),
            }
        return {
            "date": check_date,
            "is_holiday": False,
            "holiday_name": None,
            "allowed_to_submit": True,
            "message": f"{check_date} is not a USA federal holiday — submission is allowed.",
        }

    def _list_holidays(self, args: Dict[str, Any]) -> Dict[str, Any]:
        year = int(args.get("year", datetime.now().year))
        try:
            conn = _conn()
            rows = conn.execute(
                "SELECT holiday_id, holiday_date, name FROM usa_holidays "
                "WHERE year=? ORDER BY holiday_date",
                (year,),
            ).fetchall()
            conn.close()
            return {
                "year": year,
                "country": "USA",
                "count": len(rows),
                "holidays": [dict(r) for r in rows],
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _count_effective_days(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Count calendar days in [start_date, end_date] minus USA federal holidays.
        Returns effective_wfh_days — use this value for quota deduction, not raw calendar days.
        """
        start = date.fromisoformat(args.get("start_date"))
        end = date.fromisoformat(args.get("end_date"))
        total_calendar = (end - start).days + 1
        holidays_in_range = get_holidays_in_range(str(start), str(end))
        effective_days = total_calendar - len(holidays_in_range)
        return {
            "start_date": str(start),
            "end_date": str(end),
            "total_calendar_days": total_calendar,
            "holiday_days_excluded": len(holidays_in_range),
            "effective_wfh_days": effective_days,
            "holidays_in_range": holidays_in_range,
            "note": (
                "effective_wfh_days = calendar days minus USA federal holidays in the range. "
                "Always use effective_wfh_days for quota deduction — never raw calendar days."
            ),
        }
