import hashlib
import secrets

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime


class VumaActivationError(frappe.ValidationError):
    pass


def _hash_code(code):
    return hashlib.sha256(
        code.strip().upper().encode("utf-8")
    ).hexdigest()


def _format_code(raw):
    raw = raw.upper()

    return "-".join(
        raw[index:index + 4]
        for index in range(0, len(raw), 4)
    )


def _generate_activation_code():
    raw = secrets.token_hex(8).upper()

    return _format_code(raw)


def _generate_activation_id():
    return f"VUMA-ACT-{secrets.token_hex(6).upper()}"


@frappe.whitelist()
def create_activation(
    installation_id,
    device_type,
    platform,
    valid_hours=24,
):
    installation_name = frappe.db.get_value(
        "Vuma Installation",
        {"installation_id": installation_id},
        "name",
    )

    if not installation_name:
        frappe.throw(
            _("Installation was not found."),
            exc=VumaActivationError,
        )

    valid_hours = int(valid_hours)

    if valid_hours < 1 or valid_hours > 168:
        frappe.throw(
            _("Activation validity must be between 1 and 168 hours."),
            exc=VumaActivationError,
        )

    code = _generate_activation_code()

    activation = frappe.get_doc({
        "doctype": "Vuma Device Activation",
        "activation_id": _generate_activation_id(),
        "installation": installation_name,
        "device_type": device_type,
        "platform": platform,
        "status": "Pending",
        "activation_code_hash": _hash_code(code),
        "expires_at": add_to_date(
            now_datetime(),
            hours=valid_hours,
        ),
    })

    activation.insert(ignore_permissions=True)
    frappe.db.commit()

    return {
        "activation_id": activation.activation_id,
        "activation_code": code,
        "installation_id": installation_id,
        "device_type": device_type,
        "platform": platform,
        "expires_at": activation.expires_at,
    }


def validate_activation_code(
    activation_code,
    device_type,
    platform,
):
    activation_hash = _hash_code(
        activation_code
    )

    activation_name = frappe.db.get_value(
        "Vuma Device Activation",
        {
            "activation_code_hash": activation_hash,
        },
        "name",
    )

    if not activation_name:
        frappe.throw(
            _("Invalid activation code."),
            exc=VumaActivationError,
        )

    activation = frappe.get_doc(
        "Vuma Device Activation",
        activation_name,
    )

    if activation.status != "Pending":
        frappe.throw(
            _("This activation code is no longer available."),
            exc=VumaActivationError,
        )

    if activation.expires_at < now_datetime():
        activation.status = "Expired"
        activation.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.throw(
            _("This activation code has expired."),
            exc=VumaActivationError,
        )

    if activation.device_type != device_type:
        frappe.throw(
            _("Activation code is for a different device type."),
            exc=VumaActivationError,
        )

    if activation.platform != platform:
        frappe.throw(
            _("Activation code is for a different platform."),
            exc=VumaActivationError,
        )

    return activation


def consume_activation(
    activation,
    device_name,
):
    activation.status = "Used"
    activation.used_at = now_datetime()
    activation.used_by_device = device_name

    activation.save(ignore_permissions=True)

    frappe.db.commit()
