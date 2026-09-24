import re
import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime


ALLOWED_DEVICE_TYPES = {
    "Desktop",
    "Mobile",
    "POS",
    "Edge",
    "Server",
}

ALLOWED_PLATFORMS = {
    "Windows",
    "macOS",
    "Android",
    "iOS",
    "Linux",
}


class VumaDeviceRegistrationError(frappe.ValidationError):
    pass


def _clean(value):
    if value is None:
        return None

    if isinstance(value, str):
        return value.strip()

    return value


def _generate_device_id():
    for _ in range(20):
        device_id = f"VUMA-DEV-{secrets.token_hex(6).upper()}"

        if not frappe.db.exists(
            "Vuma Device",
            {"device_id": device_id},
        ):
            return device_id

    frappe.throw(
        _("Unable to generate a unique Vuma Device ID."),
        exc=VumaDeviceRegistrationError,
    )


def _get_installation(installation_id):
    installation_id = _clean(installation_id)

    if not installation_id:
        frappe.throw(
            _("Installation ID is required."),
            exc=VumaDeviceRegistrationError,
        )

    installation_name = frappe.db.get_value(
        "Vuma Installation",
        {"installation_id": installation_id},
        "name",
    )

    if not installation_name:
        frappe.throw(
            _("Vuma installation {0} was not found.").format(
                installation_id
            ),
            exc=VumaDeviceRegistrationError,
        )

    installation = frappe.get_doc(
        "Vuma Installation",
        installation_name,
    )

    if not installation.setup_complete:
        frappe.throw(
            _("This Vuma installation has not completed setup."),
            exc=VumaDeviceRegistrationError,
        )

    return installation


def _get_build(build_id):
    build_id = _clean(build_id)

    if not build_id:
        frappe.throw(
            _("Build ID is required."),
            exc=VumaDeviceRegistrationError,
        )

    build_name = frappe.db.get_value(
        "Vuma Build",
        {"build_id": build_id},
        "name",
    )

    if not build_name:
        frappe.throw(
            _("Vuma build {0} was not found.").format(build_id),
            exc=VumaDeviceRegistrationError,
        )

    build = frappe.get_doc(
        "Vuma Build",
        build_name,
    )

    if build.blocked:
        frappe.throw(
            _("Build {0} has been blocked.").format(build.build_id),
            exc=VumaDeviceRegistrationError,
        )

    if not build.active:
        frappe.throw(
            _("Build {0} is not active.").format(build.build_id),
            exc=VumaDeviceRegistrationError,
        )

    return build


def _validate_platform(build, platform):
    platform = _clean(platform)

    if platform not in ALLOWED_PLATFORMS:
        frappe.throw(
            _("Unsupported device platform: {0}").format(platform),
            exc=VumaDeviceRegistrationError,
        )

    if build.platform != platform:
        frappe.throw(
            _(
                "Build {0} is for {1}, but this device reported {2}."
            ).format(
                build.build_id,
                build.platform,
                platform,
            ),
            exc=VumaDeviceRegistrationError,
        )


def _validate_device_type(device_type):
    device_type = _clean(device_type)

    if device_type not in ALLOWED_DEVICE_TYPES:
        frappe.throw(
            _("Unsupported device type: {0}").format(device_type),
            exc=VumaDeviceRegistrationError,
        )


def _validate_public_key(public_key):
    public_key = _clean(public_key)

    if not public_key:
        frappe.throw(
            _("A device public key is required."),
            exc=VumaDeviceRegistrationError,
        )

    if len(public_key) > 10000:
        frappe.throw(
            _("The supplied public key is too large."),
            exc=VumaDeviceRegistrationError,
        )

    return public_key


def _validate_device_name(device_name):
    device_name = _clean(device_name)

    if not device_name:
        return None

    if len(device_name) > 140:
        frappe.throw(
            _("Device name cannot exceed 140 characters."),
            exc=VumaDeviceRegistrationError,
        )

    return device_name


@frappe.whitelist(allow_guest=True)
def register_device(
    installation_id,
    build_id,
    device_type,
    platform,
    public_key,
    device_name=None,
    os_version=None,
    app_version=None,
):
    """
    Register a Vuma device.

    IMPORTANT:
    The device generates its keypair locally.
    Only the public key is sent to Vuma.
    The private key must never be transmitted to this API.
    """

    installation = _get_installation(installation_id)
    build = _get_build(build_id)

    _validate_device_type(device_type)
    _validate_platform(build, platform)

    public_key = _validate_public_key(public_key)
    device_name = _validate_device_name(device_name)

    existing = frappe.db.get_value(
        "Vuma Device",
        {
            "installation": installation.name,
            "public_key": public_key,
        },
        [
            "name",
            "device_id",
            "status",
            "build",
            "platform",
        ],
        as_dict=True,
    )

    if existing:
        return {
            "registered": True,
            "existing": True,
            "device_id": existing.device_id,
            "status": existing.status,
            "platform": existing.platform,
            "build": existing.build,
        }

    device_id = _generate_device_id()

    device = frappe.get_doc(
        {
            "doctype": "Vuma Device",
            "device_id": device_id,
            "installation": installation.name,
            "build": build.name,
            "device_type": device_type,
            "platform": platform,
            "status": "Pending",
            "device_name": device_name,
            "os_version": _clean(os_version),
            "app_version": _clean(app_version),
            "public_key": public_key,
            "key_algorithm": "Ed25519",
            "registered_at": now_datetime(),
            "consumes_licence_slot": 1,
            "offline_allowed": (
                1
                if device_type in {"Mobile", "POS", "Edge"}
                else 0
            ),
        }
    )

    device.flags.ignore_permissions = True
    device.insert()

    frappe.db.commit()

    return {
        "registered": True,
        "existing": False,
        "device_id": device.device_id,
        "status": device.status,
        "installation_id": installation.installation_id,
        "build_id": build.build_id,
        "device_type": device.device_type,
        "platform": device.platform,
        "offline_allowed": bool(device.offline_allowed),
        "registered_at": device.registered_at,
    }

