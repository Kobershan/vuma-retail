from vuma.licensing.entitlements import (
    get_client_entitlements,
)


def boot_session(bootinfo):
    """
    Inject Vuma entitlement information into frappe.boot.

    Client-side code can read:
        frappe.boot.vuma
        frappe.boot.vuma.modules
        frappe.boot.vuma.entitlements
    """

    try:
        bootinfo.vuma = get_client_entitlements()

    except Exception:
        # Never break the entire Frappe Desk login because
        # Vuma licence information could not be loaded.
        bootinfo.vuma = {
            "configured": False,
            "modules": [],
            "entitlements": {},
            "error": True,
        }
