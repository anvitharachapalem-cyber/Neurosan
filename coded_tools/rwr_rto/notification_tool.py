"""
RWR-RTO Notification Tool
Logs notifications to a file (simulates email/Teams/Slack in a real deployment).
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Union

from neuro_san.interfaces.coded_tool import CodedTool

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "notifications.log")

# Notification type templates
TEMPLATES = {
    "REQUEST_SUBMITTED":       "Your WFH request {request_id} for category '{category}' has been submitted and is pending approval.",
    "REQUEST_APPROVED":        "Your WFH request {request_id} has been APPROVED. Enjoy your work-from-home days!",
    "REQUEST_REJECTED":        "Your WFH request {request_id} has been REJECTED. Reason: {reason}.",
    "AUTO_REJECTED_INACTION":  "Your WFH request {request_id} has been AUTO-REJECTED due to manager inaction. You may resubmit.",
    "AUTO_REJECTED_NO_CLARIF": "Your WFH request {request_id} has been AUTO-REJECTED as no clarification was provided in time.",
    "SEEK_CLARIFICATION":      "Additional information is required for WFH request {request_id}. Please respond by {due_date}.",
    "APPROVAL_PENDING":        "A WFH request {request_id} from {employee_name} requires your approval by {deadline}.",
    "ESCALATED_TO_SKIP":       "WFH request {request_id} has been escalated to you as skip-level manager. Please act by {deadline}.",
    "RESUBMIT_ENABLED":        "Your WFH request {request_id} was auto-rejected due to manager inaction. Click 'Resubmit' to try again.",
}


class NotificationTool(CodedTool):
    """
    CodedTool for sending notifications.

    Expected args:
        type         (str): Notification type key from TEMPLATES above.
        recipient_id (str): Employee ID of the recipient.
        request_id   (str): The WFH request ID.
        message      (str, optional): Custom message override.
        metadata     (dict, optional): Extra fields for template substitution.
    """

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        notification_type = args.get("type", "GENERIC")
        recipient_id = args.get("recipient_id", "")
        request_id = args.get("request_id", "")
        metadata = args.get("metadata", {})

        # Build message from template or use custom message
        template = TEMPLATES.get(notification_type, "{message}")
        try:
            message = args.get("message") or template.format(
                request_id=request_id, **metadata
            )
        except KeyError:
            message = args.get("message", template)

        record = {
            "timestamp": datetime.now().isoformat(),
            "type": notification_type,
            "recipient_id": recipient_id,
            "request_id": request_id,
            "message": message,
            "metadata": metadata,
        }

        # Write to log file
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

        return {
            "success": True,
            "notification_sent": True,
            "type": notification_type,
            "recipient_id": recipient_id,
            "request_id": request_id,
            "message": message,
        }
