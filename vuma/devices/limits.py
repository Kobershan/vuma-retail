import frappe
from frappe import _


DEVICE_LIMIT_FIELDS = {
    "Desktop": "licensed_desktop_devices",
    "Mobile": "licensed_mobile_devices",
    "POS": "licensed_pos_devices",
    "Edge": "licensed_edge_devices",
    "Server": "licensed_server_devices",
}


class VumaDeviceLimitError(frappe.ValidationError):
    pass


def _get_installation(installation=None):
    if installation:
        if frappe.db.exists(
            "Vuma Installation",
            installation,
        ):
            return frappe.get_doc(
                "Vuma Installation",
                installation,
            )

        installation_name = frappe.db.get_value(
            "Vuma Installation",
            {
                "installation_id": installation,
            },
            "name",
        )

        if installation_name:
            return frappe.get_doc(
                "Vuma Installation",
                installation_name,
            )

        frappe.throw(
            _("Vuma installation was not found."),
            exc=VumaDeviceLimitError,
        )

    installations = frappe.get_all(
        "Vuma Installation",
        filters={
            "setup_complete": 1,
        },
        fields=["name"],
        limit=2,
    )

    if not installations:
        frappe.throw(
            _("No completed Vuma installation was found."),
            exc=VumaDeviceLimitError,
        )

    if len(installations) > 1:
        frappe.log_error(
            title="Vuma Device Limits",
            message=(
                "Multiple completed Vuma Installation records "
                "were found. Using the first record."
            ),
        )

    return frappe.get_doc(
        "Vuma Installation",
        installations[0].name,
    )


def _get_limit(
    installation,
    device_type,
):
    fieldname = DEVICE_LIMIT_FIELDS.get(
        device_type
    )

    if not fieldname:
        frappe.throw(
            _(
                "Unsupported Vuma device type: {0}"
            ).format(device_type),
            exc=VumaDeviceLimitError,
        )

    meta = frappe.get_meta(
        "Vuma Installation"
    )

    if not meta.has_field(fieldname):
        frappe.throw(
            _(
                "Device licence field {0} "
                "does not exist on Vuma Installation."
            ).format(fieldname),
            exc=VumaDeviceLimitError,
        )

    return int(
        installation.get(fieldname)
        or 0
    )


def _get_used_count(
    installation,
    device_type,
    exclude_device=None,
):
    filters = {
        "installation": installation.name,
        "device_type": device_type,
        "status": [
            "in",
            [
                "Pending",
                "Active",
            ],
        ],
        "consumes_licence_slot": 1,
    }

    if exclude_device:
        filters["name"] = [
            "!=",
            exclude_device,
        ]

    return frappe.db.count(
        "Vuma Device",
        filters=filters,
    )


def assert_device_capacity(
    installation,
    device_type,
    exclude_device=None,
):
    if not hasattr(
        installation,
        "doctype",
    ):
        installation = _get_installation(
            installation
        )

    limit = _get_limit(
        installation,
        device_type,
    )

    used = _get_used_count(
        installation,
        device_type,
        exclude_device=exclude_device,
    )

    #
    # A zero limit means that this device
    # type is not licensed at all.
    #
    if limit <= 0:
        frappe.throw(
            _(
                "{0} devices are not licensed "
                "for this Vuma installation."
            ).format(device_type),
            exc=VumaDeviceLimitError,
        )

    if used >= limit:
        frappe.throw(
            _(
                "{0} device licence limit reached. "
                "Used: {1}, Limit: {2}."
            ).format(
                device_type,
                used,
                limit,
            ),
            exc=VumaDeviceLimitError,
        )

    return {
        "device_type": device_type,
        "used": used,
        "limit": limit,
        "remaining": limit - used,
    }


@frappe.whitelist()
def get_device_usage(
    installation=None,
):
    installation_doc = _get_installation(
        installation
    )

    usage = {}

    for (
        device_type,
        fieldname,
    ) in DEVICE_LIMIT_FIELDS.items():

        limit = int(
            installation_doc.get(
                fieldname
            )
            or 0
        )

        used = _get_used_count(
            installation_doc,
            device_type,
        )

        usage[device_type] = {
            "used": used,
            "limit": limit,
            "remaining": max(
                limit - used,
                0,
            ),
            "available": (
                limit > used
            ),
        }

    return {
        "installation_id":
            installation_doc.installation_id,
        "usage": usage,
    }
