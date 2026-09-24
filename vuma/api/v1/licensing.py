import frappe

from vuma.api.v1.responses import success
from vuma.licensing.entitlements import (
    get_client_entitlements,
    get_enabled_module_codes,
)


@frappe.whitelist()
def entitlements():
    """
    Return the current Vuma installation's
    module entitlements.
    """

    data = get_client_entitlements()

    return success(
        data=data
    )


@frappe.whitelist()
def enabled_modules():
    """
    Return a simple list of enabled Vuma module codes.
    """

    modules = get_enabled_module_codes()

    return success(
        data={
            "modules": modules,
        }
    )
