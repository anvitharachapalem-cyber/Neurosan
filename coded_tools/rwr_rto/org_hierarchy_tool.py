"""
RWR-RTO Org Hierarchy Tool
Resolves employee levels, managers, skip-level managers, and valid approvers.
"""
import os
import sqlite3
from typing import Any, Dict, List, Optional, Union

from neuro_san.interfaces.coded_tool import CodedTool
from coded_tools.rwr_rto.database_tool import initialize_database

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "rwr_rto.db")

LEVEL_RANK = {
    "C_LEVEL": 10, "SVP": 9, "EVP": 8, "VP": 7,
    "DIRECTOR": 6, "SM": 5, "MANAGER": 4,
    "ASSOCIATE": 3, "ANALYST": 2, "INTERN": 1,
}
SM_AND_ABOVE = {"SM", "DIRECTOR", "VP", "EVP", "SVP", "C_LEVEL"}
DIRECTOR_AND_ABOVE = {"DIRECTOR", "VP", "EVP", "SVP", "C_LEVEL"}


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _fetch_employee(employee_id: str) -> Optional[Dict[str, Any]]:
    conn = _conn()
    try:
        row = conn.execute("SELECT * FROM employees WHERE employee_id=?", (employee_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


class OrgHierarchyTool(CodedTool):
    """
    CodedTool for organisational hierarchy queries.

    Supported operations (pass via args["operation"]):
        get_employee_level, is_sm_or_above, is_director_or_above,
        get_manager, get_skip_level_manager, get_approver, get_reportees
    """

    def __init__(self):
        super().__init__()
        initialize_database()  # ensure DB and tables exist before any query

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        op = args.get("operation", "")
        dispatch = {
            "get_employee_level":       self._get_employee_level,
            "is_sm_or_above":           self._is_sm_or_above,
            "is_director_or_above":     self._is_director_or_above,
            "get_manager":              self._get_manager,
            "get_skip_level_manager":   self._get_skip_level_manager,
            "get_approver":             self._get_approver,
            "get_reportees":            self._get_reportees,
        }
        handler = dispatch.get(op)
        if not handler:
            return {"error": f"Unknown operation: '{op}'. Valid: {list(dispatch.keys())}"}
        return handler(args)

    # ------------------------------------------------------------------ #

    def _get_employee_level(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp = _fetch_employee(args.get("employee_id", ""))
        if not emp:
            return {"error": "Employee not found"}
        return {
            "employee_id": emp["employee_id"],
            "name": emp["name"],
            "level": emp["level"],
            "level_rank": LEVEL_RANK.get(emp["level"], 0),
        }

    def _is_sm_or_above(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp = _fetch_employee(args.get("employee_id", ""))
        if not emp:
            return {"error": "Employee not found", "is_sm_or_above": False}
        return {
            "employee_id": emp["employee_id"],
            "level": emp["level"],
            "is_sm_or_above": emp["level"] in SM_AND_ABOVE,
        }

    def _is_director_or_above(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp = _fetch_employee(args.get("employee_id", ""))
        if not emp:
            return {"error": "Employee not found", "is_director_or_above": False}
        return {
            "employee_id": emp["employee_id"],
            "level": emp["level"],
            "is_director_or_above": emp["level"] in DIRECTOR_AND_ABOVE,
        }

    def _get_manager(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp = _fetch_employee(args.get("employee_id", ""))
        if not emp:
            return {"error": "Employee not found"}
        if not emp.get("manager_id"):
            return {"manager": None, "message": "Top of hierarchy — no manager."}
        manager = _fetch_employee(emp["manager_id"])
        return {"manager": manager}

    def _get_skip_level_manager(self, args: Dict[str, Any]) -> Dict[str, Any]:
        emp = _fetch_employee(args.get("employee_id", ""))
        if not emp or not emp.get("manager_id"):
            return {"skip_level_manager": None, "message": "No manager found."}
        mgr = _fetch_employee(emp["manager_id"])
        if not mgr or not mgr.get("manager_id"):
            return {"skip_level_manager": None, "message": "No skip-level manager found."}
        skip = _fetch_employee(mgr["manager_id"])
        return {"skip_level_manager": skip}

    def _get_approver(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Walk up the hierarchy from the employee's direct manager until an SM+ is found.
        Rules:
          - If direct manager is SM+, they are the approver.
          - If direct manager is below SM, walk up until SM+ is found.
        """
        employee_id = args.get("employee_id", "")
        emp = _fetch_employee(employee_id)
        if not emp or not emp.get("manager_id"):
            return {"error": "No manager found for employee", "approver": None}

        chain: List[Dict[str, Any]] = []
        current_id: Optional[str] = emp["manager_id"]
        while current_id:
            current = _fetch_employee(current_id)
            if not current:
                break
            chain.append(current)
            if current["level"] in SM_AND_ABOVE:
                return {
                    "approver": current,
                    "approver_id": current["employee_id"],
                    "is_direct_manager": len(chain) == 1,
                    "hierarchy_chain": [c["employee_id"] for c in chain],
                }
            current_id = current.get("manager_id")

        return {"error": "No SM+ approver found in hierarchy", "approver": None}

    def _get_reportees(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = _conn()
        try:
            rows = conn.execute(
                "SELECT * FROM employees WHERE manager_id=?", (args.get("manager_id"),)
            ).fetchall()
            return {"manager_id": args.get("manager_id"), "reportees": [dict(r) for r in rows]}
        finally:
            conn.close()
