import base64
import secrets

import frappe
from frappe import _
from frappe.utils import now_datetime

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from vuma.devices.activation import (
    consume_activation,
    validate_activation_code,
)
from vuma.devices.limits import assert_device_capacity
from vuma.devices.registration import (
    _generate_device_id,
    _get_build,
    _get_installation,
    _validate_device_name,
    _validate_device_type,
    _validate_platform,
    _validate_public_key,
)


BOOTSTRAP_CHALLENGE_TTL_SECONDS = 300


class VumaDeviceBootstrapError(frappe.ValidationError):
    pass


DEVICE_APPLICATION_MAP = {
    "Desktop": "Vuma Desktop",
    "Mobile": "Vuma Mobile",
    "POS": "Vuma POS",
    "Edge": "Vuma Edge",
    "Server": "Vuma Server",
}


def _challenge_cache_key(device_id):
    return f"vuma:bootstrap-challenge:{device_id}"


def _activation_cache_key(device_id):
    return f"vuma:bootstrap-activation:{device_id}"


def _validate_build_application(build, device_type):
    expected_application = DEVICE_APPLICATION_MAP.get(device_type)

    if not expected_application:
        frappe.throw(
            _("Unsupported Vuma device type."),
            exc=VumaDeviceBootstrapError,
        )

    if build.application != expected_application:
        frappe.throw(
            _(
                "Build {0} belongs to {1}, but this device is registering "
                "as {2}."
            ).format(
                build.build_id,
                build.application,
                device_type,
            ),
            exc=VumaDeviceBootstrapError,
        )


def _get_pending_device(device_id):
    name = frappe.db.get_value(
        "Vuma Device",
        {"device_id": device_id},
        "name",
    )

    if not name:
        frappe.throw(
            _("Vuma device was not found."),
            exc=VumaDeviceBootstrapError,
        )

    device = frappe.get_doc(
        "Vuma Device",
        name,
    )

    if device.status != "Pending":
        frappe.throw(
            _("Device {0} is not awaiting activation.").format(
                device.device_id
            ),
            exc=VumaDeviceBootstrapError,
        )

    return device


@frappe.whitelist(allow_guest=True)
def start_activation(
    activation_code,
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
    Begin first-run Vuma device activation.

    The device generates its keypair locally.

    Only the PUBLIC key is sent to Vuma.
    The PRIVATE key must never leave the device.
    """

    installation = _get_installation(
        installation_id
    )

    build = _get_build(
        build_id
    )

    _validate_device_type(
        device_type
    )

    _validate_platform(
        build,
        platform,
    )

    _validate_build_application(
        build,
        device_type,
    )

    public_key = _validate_public_key(
        public_key
    )

    device_name = _validate_device_name(
        device_name
    )

    activation = validate_activation_code(
        activation_code,
        device_type,
        platform,
    )

    if activation.installation != installation.name:
        frappe.throw(
            _(
                "This activation code belongs to a different "
                "Vuma installation."
            ),
            exc=VumaDeviceBootstrapError,
        )

    #
    # First check whether this cryptographic identity already exists.
    #
    existing_name = frappe.db.get_value(
        "Vuma Device",
        {
            "installation": installation.name,
            "public_key": public_key,
        },
        "name",
    )

    if existing_name:
        existing = frappe.get_doc(
            "Vuma Device",
            existing_name,
        )

        if existing.status == "Active":
            return {
                "already_active": True,
                "device_id": existing.device_id,
                "status": existing.status,
            }

        if existing.status in {
            "Suspended",
            "Revoked",
        }:
            frappe.throw(
                _("This device identity cannot be activated."),
                exc=VumaDeviceBootstrapError,
            )

        device = existing

    else:
        #
        # Brand-new device:
        # verify the installation still has capacity
        # before creating the Pending record.
        #
        capacity = assert_device_capacity(
            installation,
            device_type,
        )

        device = frappe.get_doc({
            "doctype": "Vuma Device",
            "device_id": _generate_device_id(),
            "installation": installation.name,
            "build": build.name,
            "device_type": device_type,
            "platform": platform,
            "status": "Pending",
            "device_name": device_name,
            "os_version": (
                os_version.strip()
                if isinstance(os_version, str)
                else os_version
            ),
            "app_version": (
                app_version.strip()
                if isinstance(app_version, str)
                else app_version
            ),
            "public_key": public_key,
            "key_algorithm": "Ed25519",
            "registered_at": now_datetime(),
            "consumes_licence_slot": 1,
            "offline_allowed": (
                1
                if device_type in {
                    "Mobile",
                    "POS",
                    "Edge",
                }
                else 0
            ),
        })

        device.flags.ignore_permissions = True
        device.insert()

    challenge_bytes = secrets.token_bytes(
        32
    )

    challenge = base64.b64encode(
        challenge_bytes
    ).decode("ascii")

    frappe.cache.set_value(
        _challenge_cache_key(
            device.device_id
        ),
        challenge,
        expires_in_sec=BOOTSTRAP_CHALLENGE_TTL_SECONDS,
    )

    frappe.cache.set_value(
        _activation_cache_key(
            device.device_id
        ),
        activation.name,
        expires_in_sec=BOOTSTRAP_CHALLENGE_TTL_SECONDS,
    )

    frappe.db.commit()

    result = {
        "started": True,
        "device_id": device.device_id,
        "status": device.status,
        "challenge": challenge,
        "algorithm": "Ed25519",
        "expires_in": BOOTSTRAP_CHALLENGE_TTL_SECONDS,
        "installation_id": installation.installation_id,
        "build_id": build.build_id,
        "platform": platform,
        "device_type": device_type,
    }

    if not existing_name:
        result["capacity"] = capacity

    return result


@frappe.whitelist(allow_guest=True)
def complete_activation(
    device_id,
    signature,
):
    """
    Complete activation by proving possession
    of the registered Ed25519 private key.
    """

    device = _get_pending_device(
        device_id
    )

    challenge_encoded = frappe.cache.get_value(
        _challenge_cache_key(
            device.device_id
        )
    )

    activation_name = frappe.cache.get_value(
        _activation_cache_key(
            device.device_id
        )
    )

    if not challenge_encoded:
        frappe.throw(
            _(
                "Activation challenge has expired. "
                "Start activation again."
            ),
            exc=VumaDeviceBootstrapError,
        )

    if not activation_name:
        frappe.throw(
            _(
                "Activation session has expired. "
                "Start activation again."
            ),
            exc=VumaDeviceBootstrapError,
        )

    activation = frappe.get_doc(
        "Vuma Device Activation",
        activation_name,
    )

    if activation.status != "Pending":
        frappe.throw(
            _("Activation code is no longer valid."),
            exc=VumaDeviceBootstrapError,
        )

    try:
        challenge_bytes = base64.b64decode(
            challenge_encoded,
            validate=True,
        )

        signature_bytes = base64.b64decode(
            signature,
            validate=True,
        )

        public_key = load_pem_public_key(
            device.public_key.encode(
                "utf-8"
            )
        )

        public_key.verify(
            signature_bytes,
            challenge_bytes,
        )

    except InvalidSignature:
        frappe.throw(
            _("Device signature is invalid."),
            exc=VumaDeviceBootstrapError,
        )

    except Exception:
        frappe.throw(
            _("Unable to verify the device identity."),
            exc=VumaDeviceBootstrapError,
        )

    #
    # Cryptographic proof succeeded.
    #
    device.status = "Active"
    device.last_seen_at = now_datetime()

    device.flags.ignore_permissions = True
    device.save()

    #
    # Consume the one-time activation code.
    #
    consume_activation(
        activation,
        device.name,
    )

    #
    # Destroy one-time activation state.
    #
    frappe.cache.delete_value(
        _challenge_cache_key(
            device.device_id
        )
    )

    frappe.cache.delete_value(
        _activation_cache_key(
            device.device_id
        )
    )

    frappe.db.commit()

    return {
        "activated": True,
        "device_id": device.device_id,
        "status": device.status,
        "installation": device.installation,
        "build": device.build,
        "platform": device.platform,
        "device_type": device.device_type,
        "offline_allowed": bool(
            device.offline_allowed
        ),
    }
