import frappe

from vuma.licensing.entitlements import assert_module_enabled


@frappe.whitelist()
def manufacturing_test():
    assert_module_enabled("MFG")

    return {
        "ok": True,
        "module": "MFG",
        "message": "Manufacturing licence check passed.",
    }


@frappe.whitelist()
def inventory_test():
    assert_module_enabled("INV")

    return {
        "ok": True,
        "module": "INV",
        "message": "Inventory licence check passed.",
    }

