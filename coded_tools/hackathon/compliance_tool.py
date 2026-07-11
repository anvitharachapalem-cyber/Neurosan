"""
compliance_tool.py
Calculates RTO (Return-to-Office) compliance for an associate
for a given month, based on their cog_work_model and level group.

Compliance thresholds:
────────────────────────────────────────────────────────────────────
SENIOR GRADES: D, SD, AVP, VP, SVP
  Cog hybrid 2/3 days        → min 80% attendance
  Cog office based 4/5 days  → min 85% attendance
  Cog remote 0/1 days        → min  5% attendance
  Cog CLT RMT                → min 100% attendance

JUNIOR GRADES: AD, SM, M, SA, A, PA, PAT, AT (and all others)
  Cog hybrid 2/3 days        → min 70% attendance
  Cog office based 4/5 days  → min 80% attendance
  Cog remote 0/1 days        →      0% (always compliant)
  Cog CLT RMT                → min 95% attendance
────────────────────────────────────────────────────────────────────
Compliance % = (days attended / total business days in month) * 100
"""
import sqlite3
import os
from typing import Any

DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "database", "hackathon", "hackathon.db"
)

SENIOR_GRADES = {"D", "SD", "AVP", "VP", "SVP"}

# (senior_threshold, junior_threshold)
THRESHOLDS = {
    "Cog hybrid 2/3 days":       (80.0, 70.0),
    "Cog office based 4/5 days": (85.0, 80.0),
    "Cog remote 0/1 days":       (5.0,   0.0),
    "Cog CLT RMT":               (100.0, 95.0),
}

MONTH_ABBR = {
    "jan": "Jan", "january": "Jan",
    "feb": "Feb", "february": "Feb",
    "mar": "Mar", "march": "Mar",
    "apr": "Apr", "april": "Apr",
    "may": "May",
    "jun": "Jun", "june": "Jun",
    "jul": "Jul", "july": "Jul",
}


class ComplianceTool:
    """Checks RTO compliance for an associate for a given month."""

    def get_instructions(self) -> str:
        return (
            "Use this tool to check an associate's office attendance compliance "
            "for a specific month. Provide associate_id and month (e.g. 'June', 'Jul'). "
            "Returns compliance %, required threshold, and compliant/non-compliant status."
        )

    def invoke(self, args: dict[str, Any]) -> dict[str, Any]:
        associate_id = args.get("associate_id")
        month = str(args.get("month", "")).strip().lower()

        if not associate_id:
            return {"error": "associate_id is required"}
        if not month:
            return {"error": "month is required (e.g. 'June', 'Jul', 'February')"}

        month_label = MONTH_ABBR.get(month[:3])
        if not month_label:
            return {"error": f"Unrecognised month '{month}'. Use Jan-Jul."}

        try:
            db_path = os.path.normpath(DB_PATH)
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            # Get associate profile
            assoc = conn.execute(
                "SELECT associate_id, associate_name, level, cog_work_model "
                "FROM associates WHERE associate_id = ?",
                (int(associate_id),)
            ).fetchone()

            if not assoc:
                conn.close()
                return {"error": f"Associate {associate_id} not found"}

            level = assoc["level"]
            wm = assoc["cog_work_model"]
            is_senior = level in SENIOR_GRADES

            # Count attendance days for the month
            days_attended = conn.execute(
                "SELECT COUNT(*) FROM attendance "
                "WHERE associate_id = ? AND month_label = ?",
                (int(associate_id), month_label)
            ).fetchone()[0]

            # Count total business days available in that month from attendance data
            # (use the max any associate has for that month as the business-day count)
            total_biz_days = conn.execute(
                "SELECT MAX(cnt) FROM ("
                "  SELECT associate_id, COUNT(*) as cnt FROM attendance "
                "  WHERE month_label = ? GROUP BY associate_id"
                ")",
                (month_label,)
            ).fetchone()[0] or 0

            conn.close()

            if total_biz_days == 0:
                return {"error": f"No attendance data found for month '{month_label}'"}

            actual_pct = round((days_attended / total_biz_days) * 100, 1)

            thresholds = THRESHOLDS.get(wm)
            if not thresholds:
                return {"error": f"Unknown work model '{wm}'"}

            required_pct = thresholds[0] if is_senior else thresholds[1]
            is_compliant = actual_pct >= required_pct

            # Days needed to be compliant
            days_needed = max(0, int((required_pct / 100) * total_biz_days) - days_attended)

            return {
                "associate_id": assoc["associate_id"],
                "associate_name": assoc["associate_name"],
                "level": level,
                "grade_group": "Senior" if is_senior else "Junior",
                "cog_work_model": wm,
                "month": month_label,
                "total_business_days": total_biz_days,
                "days_attended": days_attended,
                "attendance_percentage": actual_pct,
                "required_percentage": required_pct,
                "is_compliant": is_compliant,
                "compliance_status": "Compliant ✅" if is_compliant else "Non-Compliant ❌",
                "days_short": days_needed if not is_compliant else 0,
                "message": (
                    f"{assoc['associate_name']} attended {days_attended}/{total_biz_days} days "
                    f"in {month_label} ({actual_pct}%). Required: {required_pct}% for {wm}. "
                    f"Status: {'Compliant ✅' if is_compliant else f'Non-Compliant ❌ — {days_needed} more day(s) needed'}"
                )
            }
        except Exception as e:
            return {"error": str(e)}
