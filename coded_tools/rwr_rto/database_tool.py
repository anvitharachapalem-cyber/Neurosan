"""
RWR-RTO Database Tool
Handles all SQLite database operations for the Remote Work Requester - Return To Office system.
"""
import os
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "rwr_rto.db")

CATEGORY_LIMITS = {
    "MEDICAL_SELF":        {"days": 14,  "type": "calendar", "unlimited": False},
    "DEPENDENT_CARE":      {"days": 7,   "type": "calendar", "unlimited": False},
    "LOCALIZED_EXIGENCY":  {"days": 7,   "type": "calendar", "unlimited": False},
    "OFFICE_TRAVEL":       {"days": 2,   "type": "business", "unlimited": False},
    "MATERNITY_RETURNEE":  {"days": 180, "type": "calendar", "unlimited": True},
    "EXTRAORDINARY":       {"days": 180, "type": "calendar", "unlimited": True},
}


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create tables and load seed data on first run."""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "schema.sql")
    seed_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "seed_data.sql")
    conn = get_connection()
    cursor = conn.cursor()
    if os.path.exists(schema_path):
        with open(schema_path, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
    cursor.execute("SELECT COUNT(*) FROM employees")
    needs_employees = cursor.fetchone()[0] == 0
    try:
        cursor.execute("SELECT COUNT(*) FROM usa_holidays")
        needs_holidays = cursor.fetchone()[0] == 0
    except Exception:
        needs_holidays = True
    if (needs_employees or needs_holidays) and os.path.exists(seed_path):
        with open(seed_path, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
    conn.commit()
    conn.close()


class DatabaseTool(CodedTool):
    """
    CodedTool for all RWR-RTO database operations.

    Supported operations (pass via args["operation"]):
        create_request, get_request, update_request_status,
        get_days_balance, update_days_balance,
        create_approval, create_clarification, respond_clarification, get_clarification,
        get_employee, list_requests, get_reportees
    """

    def __init__(self):
        super().__init__()
        initialize_database()

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        op = args.get("operation", "")
        dispatch = {
            "create_request":         self._create_request,
            "get_request":            self._get_request,
            "update_request_status":  self._update_request_status,
            "get_days_balance":       self._get_days_balance,
            "update_days_balance":    self._update_days_balance,
            "create_approval":        self._create_approval,
            "create_clarification":   self._create_clarification,
            "respond_clarification":  self._respond_clarification,
            "get_clarification":      self._get_clarification,
            "get_employee":           self._get_employee,
            "list_requests":          self._list_requests,
            "get_reportees":          self._get_reportees,
        }
        handler = dispatch.get(op)
        if not handler:
            return {"error": f"Unknown operation: '{op}'. Valid: {list(dispatch.keys())}"}
        return handler(args)

    # ------------------------------------------------------------------ #
    #  Requests                                                            #
    # ------------------------------------------------------------------ #

    def _create_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            # Enforce: WFH requests cannot start on a USA federal holiday
            start_date = args.get("start_date", "")
            if start_date:
                try:
                    holiday_row = conn.execute(
                        "SELECT name FROM usa_holidays WHERE holiday_date=?", (start_date,)
                    ).fetchone()
                    if holiday_row:
                        return {
                            "error": (
                                f"Cannot submit WFH request. '{start_date}' is a USA federal holiday: "
                                f"{holiday_row['name']}. Please choose a different start date."
                            ),
                            "start_date": start_date,
                            "holiday_name": holiday_row["name"],
                            "allowed_to_submit": False,
                        }
                except Exception:
                    pass  # usa_holidays table not yet available; proceed without check

            request_id = str(uuid.uuid4())[:8].upper()
            now = datetime.now().isoformat()
            conn.execute(
                """INSERT INTO wfh_requests
                   (request_id, employee_id, requester_id, category, days_requested,
                    start_date, end_date, status, created_at, updated_at, notes, can_resubmit)
                   VALUES (?,?,?,?,?,?,?,'PENDING',?,?,?,0)""",
                (
                    request_id,
                    args.get("employee_id"),
                    args.get("requester_id", args.get("employee_id")),
                    args.get("category"),
                    args.get("days_requested"),
                    args.get("start_date"),
                    args.get("end_date"),
                    now, now,
                    args.get("notes", ""),
                ),
            )
            conn.commit()
            return {"success": True, "request_id": request_id, "status": "PENDING", "created_at": now}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}
        finally:
            conn.close()

    def _get_request(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM wfh_requests WHERE request_id = ?", (args.get("request_id"),)
            ).fetchone()
            return dict(row) if row else {"error": "Request not found"}
        finally:
            conn.close()

    def _update_request_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            now = datetime.now().isoformat()
            allowed_fields = [
                "status", "approver_id", "skip_level_manager_id",
                "escalated_at", "auto_reject_reason", "can_resubmit", "rejection_reason",
            ]
            fields = ["updated_at = ?"]
            values = [now]
            for field in allowed_fields:
                if field in args:
                    if field == "can_resubmit":
                        val = args[field]
                        # LLMs sometimes pass booleans as strings e.g. "false"
                        if isinstance(val, str):
                            int_val = 1 if val.lower() in ("true", "1", "yes") else 0
                        else:
                            int_val = 1 if val else 0
                        fields.append(f"{field} = ?")
                        values.append(int_val)
                    else:
                        fields.append(f"{field} = ?")
                        values.append(args[field])
            values.append(args.get("request_id"))
            conn.execute(
                f"UPDATE wfh_requests SET {', '.join(fields)} WHERE request_id = ?", values
            )
            conn.commit()
            return {"success": True, "request_id": args.get("request_id"), "new_status": args.get("status")}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}
        finally:
            conn.close()

    def _list_requests(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            query = "SELECT * FROM wfh_requests WHERE 1=1"
            params: list = []
            if "employee_id" in args:
                query += " AND employee_id = ?"
                params.append(args["employee_id"])
            if "status" in args:
                query += " AND status = ?"
                params.append(args["status"])
            query += " ORDER BY created_at DESC"
            rows = conn.execute(query, params).fetchall()
            return {"requests": [dict(r) for r in rows]}
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Days Balance                                                        #
    # ------------------------------------------------------------------ #

    def _get_days_balance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            employee_id = args.get("employee_id")
            category = args.get("category")
            fiscal_year = args.get("fiscal_year", datetime.now().year)
            row = conn.execute(
                "SELECT * FROM days_balance WHERE employee_id=? AND category=? AND fiscal_year=?",
                (employee_id, category, fiscal_year),
            ).fetchone()
            limit_info = CATEGORY_LIMITS.get(category, {})
            if row:
                data = dict(row)
                data["days_remaining"] = max(0, data["days_limit"] - data["days_used"])
                data["is_unlimited"] = bool(limit_info.get("unlimited", False))
                return data
            return {
                "employee_id": employee_id,
                "category": category,
                "days_used": 0,
                "days_limit": limit_info.get("days", 0),
                "is_unlimited": limit_info.get("unlimited", False),
                "days_remaining": limit_info.get("days", 0),
                "fiscal_year": fiscal_year,
            }
        finally:
            conn.close()

    def _update_days_balance(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            employee_id = args.get("employee_id")
            category = args.get("category")
            days_to_add = args.get("days_to_add", 0)
            fiscal_year = args.get("fiscal_year", datetime.now().year)
            limit_info = CATEGORY_LIMITS.get(category, {})
            conn.execute(
                """INSERT INTO days_balance (balance_id, employee_id, category, days_used, days_limit, is_unlimited, fiscal_year)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(employee_id, category, fiscal_year) DO UPDATE SET days_used = days_used + ?""",
                (
                    str(uuid.uuid4())[:8].upper(),
                    employee_id, category, days_to_add,
                    limit_info.get("days", 0),
                    1 if limit_info.get("unlimited", False) else 0,
                    fiscal_year, days_to_add,
                ),
            )
            conn.commit()
            return {"success": True}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Approvals                                                           #
    # ------------------------------------------------------------------ #

    def _create_approval(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            approval_id = str(uuid.uuid4())[:8].upper()
            conn.execute(
                """INSERT INTO approvals (approval_id, request_id, approver_id, action, action_date, comments, deadline)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    approval_id,
                    args.get("request_id"),
                    args.get("approver_id"),
                    args.get("action"),
                    datetime.now().isoformat(),
                    args.get("comments", ""),
                    args.get("deadline", ""),
                ),
            )
            conn.commit()
            return {"success": True, "approval_id": approval_id}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Clarifications                                                      #
    # ------------------------------------------------------------------ #

    def _create_clarification(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            clarification_id = str(uuid.uuid4())[:8].upper()
            conn.execute(
                """INSERT INTO clarifications
                   (clarification_id, request_id, approver_id, question, required_docs, due_date, status)
                   VALUES (?,?,?,?,?,?,'PENDING')""",
                (
                    clarification_id,
                    args.get("request_id"),
                    args.get("approver_id"),
                    args.get("question"),
                    args.get("required_docs", ""),
                    args.get("due_date"),
                ),
            )
            conn.commit()
            return {"success": True, "clarification_id": clarification_id}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}
        finally:
            conn.close()

    def _respond_clarification(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE clarifications SET response=?, responded_at=?, status='RESPONDED' WHERE clarification_id=?",
                (args.get("response"), datetime.now().isoformat(), args.get("clarification_id")),
            )
            conn.commit()
            return {"success": True}
        except Exception as exc:  # pylint: disable=broad-except
            return {"error": str(exc)}
        finally:
            conn.close()

    def _get_clarification(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM clarifications WHERE request_id=? ORDER BY rowid DESC LIMIT 1",
                (args.get("request_id"),),
            ).fetchone()
            return dict(row) if row else {"error": "No clarification found for this request"}
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    #  Employees                                                           #
    # ------------------------------------------------------------------ #

    def _get_employee(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM employees WHERE employee_id=?", (args.get("employee_id"),)
            ).fetchone()
            return dict(row) if row else {"error": f"Employee {args.get('employee_id')} not found"}
        finally:
            conn.close()

    def _get_reportees(self, args: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM employees WHERE manager_id=?", (args.get("manager_id"),)
            ).fetchall()
            return {"reportees": [dict(r) for r in rows]}
        finally:
            conn.close()
