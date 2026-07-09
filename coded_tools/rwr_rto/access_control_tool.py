"""
RWR-RTO Access Control Tool
Enforces Director-and-above access and on-behalf-of eligibility rules.
"""
import os
import sqlite3
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.rwr_rto.database_tool import initialize_database

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "rwr_rto.db")

DIRECTOR_AND_ABOVE = {"DIRECTOR", "VP", "EVP", "SVP", "C_LEVEL"}
ON_BEHALF_ALLOWED_CATEGORY = "MEDICAL_SELF"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _fetch(employee_id: str):
    conn = _conn()
    try:
        row = conn.execute("SELECT * FROM employees WHERE employee_id=?", (employee_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


class AccessControlTool(CodedTool):
    """
    CodedTool for access control.

    Supported operations (pass via args["operation"]):
        check_access        — verify employee is Director or above
        check_on_behalf_of  — verify DRM raising request on behalf of reportee (MEDICAL_SELF only)
    """

    def __init__(self):
        super().__init__()
        initialize_database()  # ensure DB and tables exist before any query

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        op = args.get("operation", "check_access")
        if op == "check_access":
            return self._check_access(args)
        if op == "check_on_behalf_of":
            return self._check_on_behalf_of(args)
        return {"error": f"Unknown operation: '{op}'. Valid: check_access, check_on_behalf_of"}

    def _check_access(self, args: Dict[str, Any]) -> Dict[str, Any]:
        employee_id = args.get("employee_id", "")
        emp = _fetch(employee_id)
        if not emp:
            return {"has_access": False, "reason": f"Employee ID '{employee_id}' not found."}
        country = emp.get("country", "").upper()
        if country != "USA":
            return {
                "has_access": False,
                "employee_id": employee_id,
                "name": emp.get("name"),
                "country": country,
                "reason": (
                    f"Access denied. The RWR-RTO system is only available to employees based in the USA. "
                    f"{emp['name']} is registered under country '{country}'."
                ),
            }
        level = emp.get("level", "")
        has_access = level in DIRECTOR_AND_ABOVE
        return {
            "employee_id": employee_id,
            "name": emp.get("name"),
            "level": level,
            "country": country,
            "has_access": has_access,
            "reason": (
                f"Access granted. {emp['name']} is a {level} based in {country}."
                if has_access
                else f"Access denied. This application is restricted to Director and above. "
                     f"{emp['name']} is a {level}."
            ),
        }

    def _check_on_behalf_of(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rules:
        - Only the Direct Reporting Manager (DRM) may raise requests on behalf of a reportee.
        - On-behalf-of is permitted ONLY for the MEDICAL_SELF category.
        """
        requester_id = args.get("requester_id", "")
        employee_id = args.get("employee_id", "")
        category = args.get("category", "")

        if requester_id == employee_id:
            return {"allowed": True, "reason": "Self-request — no on-behalf-of constraint."}

        if category != ON_BEHALF_ALLOWED_CATEGORY:
            return {
                "allowed": False,
                "reason": (
                    f"On-behalf-of requests are only allowed for '{ON_BEHALF_ALLOWED_CATEGORY}'. "
                    f"Category '{category}' is not eligible."
                ),
            }

        emp = _fetch(employee_id)
        if not emp:
            return {"allowed": False, "reason": f"Employee '{employee_id}' not found."}

        if emp.get("manager_id") != requester_id:
            return {
                "allowed": False,
                "reason": (
                    f"Only the direct reporting manager may raise requests on behalf of an associate. "
                    f"Requester '{requester_id}' is not the direct manager of '{employee_id}'."
                ),
            }

        return {
            "allowed": True,
            "reason": (
                f"'{requester_id}' is the direct reporting manager of '{employee_id}' "
                f"and category is '{ON_BEHALF_ALLOWED_CATEGORY}'."
            ),
            "requester_id": requester_id,
            "employee_id": employee_id,
        }
