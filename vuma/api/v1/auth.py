import frappe
from frappe import _

from vuma.api.v1.responses import success


@frappe.whitelist()
def me():
    """
    Return information about the currently
    authenticated Vuma user.
    """

    user = frappe.session.user

    if not user or user == "Guest":
        frappe.throw(
            _("Authentication required."),
            frappe.AuthenticationError,
        )

    user_doc = frappe.get_doc(
        "User",
        user,
    )

    return success(
        data={
            "user": user,
            "full_name": user_doc.full_name,
            "enabled": bool(user_doc.enabled),
            "user_type": user_doc.user_type,
            "roles": frappe.get_roles(user),
        }
    )


@frappe.whitelist()
def session():
    """
    Small session check suitable for clients.
    """

    user = frappe.session.user

    authenticated = bool(
        user and user != "Guest"
    )

    return success(
        data={
            "authenticated": authenticated,
            "user": (
                user
                if authenticated
                else None
            ),
        }
    )
