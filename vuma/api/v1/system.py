import frappe
from frappe.utils import now_datetime

from vuma.api.v1.responses import success


@frappe.whitelist(allow_guest=True)
def health():
    """
    Lightweight public health check.

    Do not expose database credentials, paths,
    installed apps or other sensitive information here.
    """

    return success(
        data={
            "service": "Vuma Retail",
            "status": "ok",
            "timestamp": str(now_datetime()),
        }
    )


@frappe.whitelist()
def system_info():
    """
    Authenticated system information for Vuma clients.
    """

    installation = frappe.get_all(
        "Vuma Installation",
        filters={
            "setup_complete": 1,
        },
        fields=[
            "name",
            "installation_id",
            "installation_name",
            "licence_status",
            "software_version",
        ],
        limit=1,
    )

    installation_data = (
        installation[0]
        if installation
        else None
    )

    return success(
        data={
            "installation": installation_data,
            "user": frappe.session.user,
        }
    )

