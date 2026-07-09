"""
RWR-RTO Resubmit Checker Tool
Determines whether the 'Resubmit' button should be enabled for a rejected request.
"""
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

# Auto-rejection reasons that ALLOW resubmission
RESUBMIT_ALLOWED = {"MANAGER_INACTION", "SKIP_LEVEL_INACTION"}

# Auto-rejection reasons that DENY resubmission
RESUBMIT_DENIED = {"ASSOCIATE_NO_CLARIFICATION"}


class ResubmitCheckerTool(CodedTool):
    """
    CodedTool that determines whether a rejected WFH request can be resubmitted.

    Rules:
      - AUTO_REJECTED + reason in RESUBMIT_ALLOWED  → can_resubmit = True
      - AUTO_REJECTED + ASSOCIATE_NO_CLARIFICATION  → can_resubmit = False
      - REJECTED by manager                          → can_resubmit = False

    Expected args:
        status             (str): Current request status.
        auto_reject_reason (str): Set when status is AUTO_REJECTED.
        rejection_reason   (str): Set when status is REJECTED by manager.
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        status = args.get("status", "")
        auto_reject_reason = args.get("auto_reject_reason", "")
        rejection_reason = args.get("rejection_reason", "")

        if status not in ("AUTO_REJECTED", "REJECTED"):
            return {
                "can_resubmit": False,
                "reason": f"Status is '{status}'. Resubmit only applies to rejected requests.",
            }

        if status == "AUTO_REJECTED":
            if auto_reject_reason in RESUBMIT_ALLOWED:
                return {
                    "can_resubmit": True,
                    "reason": (
                        f"Request was auto-rejected due to manager inaction "
                        f"(reason: {auto_reject_reason}). "
                        f"Associate is eligible to resubmit."
                    ),
                }
            if auto_reject_reason == "ASSOCIATE_NO_CLARIFICATION":
                return {
                    "can_resubmit": False,
                    "reason": (
                        "Request was auto-rejected because the associate did not provide "
                        "the requested clarification in time. Resubmit is NOT allowed. "
                        "Associate must raise a brand-new request."
                    ),
                }
            return {
                "can_resubmit": False,
                "reason": f"Auto-rejection reason '{auto_reject_reason}' does not qualify for resubmit.",
            }

        # status == "REJECTED" (by manager)
        return {
            "can_resubmit": False,
            "reason": (
                f"Request was manually rejected by the approving manager "
                f"(reason: {rejection_reason or 'not specified'}). "
                f"Resubmit is NOT allowed. Associate may raise a new request."
            ),
        }
