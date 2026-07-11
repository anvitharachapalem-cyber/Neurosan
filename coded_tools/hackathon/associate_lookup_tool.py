"""
associate_lookup_tool.py
Looks up associate profile from the DB given an associate_id.
Returns name, level, cog_work_model, country, city, supervisor, account.
"""
import sqlite3
import os
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get(
    "HACKATHON_DB",
    os.path.normpath(os.path.join(_HERE, "..", "..", "database", "hackathon", "hackathon.db"))
)


class AssociateLookupTool:
    """Retrieves full associate profile from associates table."""

    def get_instructions(self) -> str:
        return (
            "Use this tool to look up an associate's profile given their associate_id. "
            "Returns name, level, work model, country, city, account and supervisor details."
        )

    def invoke(self, args: dict[str, Any]) -> dict[str, Any]:
        associate_id = args.get("associate_id")
        if not associate_id:
            return {"error": "associate_id is required"}

        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """SELECT associate_id, associate_name, account, supervisor_name,
                          supervisor_id, level, country, city, office_name,
                          cog_work_model, work_model, compliant_status, compliance_score
                   FROM associates WHERE associate_id = ?""",
                (int(associate_id),)
            ).fetchone()
            conn.close()

            if not row:
                return {
                    "found": False,
                    "message": f"No associate found with ID {associate_id}. "
                               "Please verify your Associate ID and try again."
                }

            return {
                "found": True,
                "associate_id": row["associate_id"],
                "associate_name": row["associate_name"],
                "level": row["level"],
                "cog_work_model": row["cog_work_model"],
                "work_model_original": row["work_model"],
                "account": row["account"],
                "supervisor_name": row["supervisor_name"],
                "supervisor_id": row["supervisor_id"],
                "country": row["country"],
                "city": row["city"],
                "office_name": row["office_name"],
                "feb_compliant_status": row["compliant_status"],
                "feb_compliance_score": round((row["compliance_score"] or 0) * 100, 1),
            }
        except Exception as e:
            return {"error": str(e)}
