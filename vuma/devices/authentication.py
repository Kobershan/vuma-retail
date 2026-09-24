import base64
import secrets

import frappe
from frappe import _
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import load_pem_public_key


CHALLENGE_TTL_SECONDS = 300


class VumaDeviceAuthenticationError(frappe.AuthenticationError):
    pass


def _challenge_cache_key(device_id):
    return f"vuma:device-challenge:{device_id}"


def _get_active_device(device_id):
    device_name = frappe.db.get_value(
        "Vuma Device",
        {"device_id": device_id},
        "name",
    )

    if not device_name:
        frappe.throw(
            _("Unknown Vuma device."),
            exc=VumaDeviceAuthenticationError,
        )

    device = frappe.get_doc(
        "Vuma Device",
        device_name,
    )

    if device.status != "Active":
        frappe.throw(
            _("This Vuma device is not active."),
            exc=VumaDeviceAuthenticationError,
        )

    build = frappe.get_doc(
        "Vuma Build",
        device.build,
    )

    if not build.active or build.blocked:
        frappe.throw(
            _("This Vuma build is not permitted."),
            exc=VumaDeviceAuthenticationError,
        )

    return device


@frappe.whitelist(allow_guest=True)
def create_challenge(device_id):
    device = _get_active_device(device_id)

    challenge = secrets.token_bytes(32)
    encoded_challenge = base64.b64encode(challenge).decode("ascii")

    frappe.cache.set_value(
        _challenge_cache_key(device.device_id),
        encoded_challenge,
        expires_in_sec=CHALLENGE_TTL_SECONDS,
    )

    return {
        "device_id": device.device_id,
        "challenge": encoded_challenge,
        "algorithm": "Ed25519",
        "expires_in": CHALLENGE_TTL_SECONDS,
    }


@frappe.whitelist(allow_guest=True)
def verify_challenge(device_id, signature):
    device = _get_active_device(device_id)

    encoded_challenge = frappe.cache.get_value(
        _challenge_cache_key(device.device_id),
    )

    if not encoded_challenge:
        frappe.throw(
            _("Device challenge has expired or does not exist."),
            exc=VumaDeviceAuthenticationError,
        )

    try:
        challenge = base64.b64decode(
            encoded_challenge,
            validate=True,
        )

        signature_bytes = base64.b64decode(
            signature,
            validate=True,
        )

        public_key = load_pem_public_key(
            device.public_key.encode("utf-8")
        )

        public_key.verify(
            signature_bytes,
            challenge,
        )

    except InvalidSignature:
        frappe.throw(
            _("Device signature is invalid."),
            exc=VumaDeviceAuthenticationError,
        )

    except Exception:
        frappe.throw(
            _("Unable to verify device identity."),
            exc=VumaDeviceAuthenticationError,
        )

    # One-time challenge: immediately destroy it after success.
    frappe.cache.delete_value(
        _challenge_cache_key(device.device_id)
    )

    frappe.db.set_value(
        "Vuma Device",
        device.name,
        "last_seen_at",
        frappe.utils.now_datetime(),
        update_modified=False,
    )

    frappe.db.commit()

    return {
        "authenticated": True,
        "device_id": device.device_id,
        "platform": device.platform,
        "device_type": device.device_type,
        "build": device.build,
    }

