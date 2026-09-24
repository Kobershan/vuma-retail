import frappe

from vuma.api.v1.responses import success
from vuma.devices.bootstrap import (
    complete_activation as bootstrap_complete_activation,
)
from vuma.devices.bootstrap import (
    start_activation as bootstrap_start_activation,
)
from vuma.devices.limits import (
    get_device_usage,
)


@frappe.whitelist()
def usage(
    installation=None,
):
    """
    Return device licence usage for the installation.
    """

    data = get_device_usage(
        installation=installation
    )

    return success(
        data=data
    )


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
    Public first-run device activation endpoint.

    A valid one-time activation code and
    cryptographic device identity are required.
    """

    data = bootstrap_start_activation(
        activation_code=activation_code,
        installation_id=installation_id,
        build_id=build_id,
        device_type=device_type,
        platform=platform,
        public_key=public_key,
        device_name=device_name,
        os_version=os_version,
        app_version=app_version,
    )

    return success(
        data=data
    )


@frappe.whitelist(allow_guest=True)
def complete_activation(
    device_id,
    signature,
):
    """
    Finish first-run activation after the device
    proves possession of its private key.
    """

    data = bootstrap_complete_activation(
        device_id=device_id,
        signature=signature,
    )

    return success(
        data=data
    )
