"""
RWR-RTO Business Days Tool
Calculates business days, escalation deadlines, and auto-reject windows.
"""
from datetime import date, datetime, timedelta
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

# USA Federal Holidays 2025-2027 (matches usa_holidays DB table)
HOLIDAYS = {
    # 2025
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26", "2025-06-19",
    "2025-07-04", "2025-09-01", "2025-10-13", "2025-11-11", "2025-11-27", "2025-12-25",
    # 2026
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25", "2026-06-19",
    "2026-07-03", "2026-09-07", "2026-10-12", "2026-11-11", "2026-11-26", "2026-12-25",
    # 2027
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-05-31", "2027-06-18",
    "2027-07-05", "2027-09-06", "2027-10-11", "2027-11-11", "2027-11-25", "2027-12-24",
}

MANAGER_ACTION_DAYS = 2       # business days before escalation to skip-level
SKIP_LEVEL_ACTION_DAYS = 2    # business days before auto-rejection


def _is_business_day(d: date) -> bool:
    return d.weekday() < 5 and d.strftime("%Y-%m-%d") not in HOLIDAYS


def _add_business_days(start: date, n: int) -> date:
    current = start
    added = 0
    while added < n:
        current += timedelta(days=1)
        if _is_business_day(current):
            added += 1
    return current


def _count_business_days(start: date, end: date) -> int:
    count = 0
    current = start
    while current < end:
        if _is_business_day(current):
            count += 1
        current += timedelta(days=1)
    return count


class BusinessDaysTool(CodedTool):
    """
    CodedTool for business-day calculations used in escalation and auto-rejection logic.

    Supported operations (pass via args["operation"]):
        add_business_days, count_business_days,
        get_escalation_deadline, is_escalation_due,
        get_auto_reject_deadline, is_auto_reject_due,
        is_business_day
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        op = args.get("operation", "")
        dispatch = {
            "add_business_days":          self._add_business_days,
            "count_business_days":        self._count_business_days,
            "get_escalation_deadline":    self._get_escalation_deadline,
            "is_escalation_due":          self._is_escalation_due,
            "get_auto_reject_deadline":   self._get_auto_reject_deadline,
            "is_auto_reject_due":         self._is_auto_reject_due,
            "is_business_day":            self._is_business_day,
        }
        handler = dispatch.get(op)
        if not handler:
            return {"error": f"Unknown operation: '{op}'. Valid: {list(dispatch.keys())}"}
        return handler(args)

    def _add_business_days(self, args: Dict[str, Any]) -> Dict[str, Any]:
        start = date.fromisoformat(args.get("start_date", datetime.now().date().isoformat()))
        n = int(args.get("business_days", 2))
        result = _add_business_days(start, n)
        return {"start_date": str(start), "business_days_added": n, "result_date": result.isoformat()}

    def _count_business_days(self, args: Dict[str, Any]) -> Dict[str, Any]:
        start = date.fromisoformat(args.get("start_date"))
        end = date.fromisoformat(args.get("end_date"))
        return {"start_date": str(start), "end_date": str(end), "business_days": _count_business_days(start, end)}

    def _get_escalation_deadline(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Return the date by which the approving manager must act before escalation."""
        submitted = datetime.fromisoformat(args.get("submitted_at", datetime.now().isoformat())).date()
        deadline = _add_business_days(submitted, MANAGER_ACTION_DAYS)
        return {
            "submitted_at": str(submitted),
            "escalation_deadline": deadline.isoformat(),
            "business_days_allowed": MANAGER_ACTION_DAYS,
        }

    def _is_escalation_due(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check whether 2 business days have elapsed since submission with no action."""
        submitted = datetime.fromisoformat(args.get("submitted_at")).date()
        today = datetime.now().date()
        elapsed = _count_business_days(submitted, today)
        return {
            "submitted_at": str(submitted),
            "today": today.isoformat(),
            "business_days_elapsed": elapsed,
            "escalation_due": elapsed >= MANAGER_ACTION_DAYS,
        }

    def _get_auto_reject_deadline(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Return the date by which the skip-level manager must act before auto-rejection."""
        escalated = datetime.fromisoformat(args.get("escalated_at", datetime.now().isoformat())).date()
        deadline = _add_business_days(escalated, SKIP_LEVEL_ACTION_DAYS)
        return {
            "escalated_at": str(escalated),
            "auto_reject_deadline": deadline.isoformat(),
            "business_days_allowed": SKIP_LEVEL_ACTION_DAYS,
        }

    def _is_auto_reject_due(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check whether 2 business days have elapsed since skip-level escalation with no action."""
        escalated = datetime.fromisoformat(args.get("escalated_at")).date()
        today = datetime.now().date()
        elapsed = _count_business_days(escalated, today)
        return {
            "escalated_at": str(escalated),
            "today": today.isoformat(),
            "business_days_elapsed": elapsed,
            "auto_reject_due": elapsed >= SKIP_LEVEL_ACTION_DAYS,
        }

    def _is_business_day(self, args: Dict[str, Any]) -> Dict[str, Any]:
        d = date.fromisoformat(args.get("date", datetime.now().date().isoformat()))
        return {"date": str(d), "is_business_day": _is_business_day(d)}
