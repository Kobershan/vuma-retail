import frappe
from frappe import _


class VumaEntitlementError(frappe.PermissionError):
    pass


def get_installation():
    """
    Return the active local Vuma Installation.

    A customer installation should normally contain exactly one
    completed Vuma Installation record.
    """

    installations = frappe.get_all(
        "Vuma Installation",
        filters={
            "setup_complete": 1,
        },
        fields=[
            "name",
            "installation_id",
            "installation_name",
            "customer_name",
            "licence_status",
            "licence_valid_from",
            "licence_valid_until",
            "grace_until",
            "licensed_user_count",
            "licensed_pos_count",
            "company_count",
            "location_count",
            "integrity_status",
        ],
        order_by="creation asc",
        limit_page_length=2,
    )

    if not installations:
        return None

    if len(installations) > 1:
        frappe.log_error(
            title="Multiple Vuma installations detected",
            message=(
                "This Vuma site contains more than one completed "
                "Vuma Installation record."
            ),
        )

    return installations[0]


def get_enabled_entitlements():
    """
    Return enabled module entitlements for the local installation.

    Keyed by the stable Vuma module code:
        ACC
        POS
        INV
        etc.
    """

    installation = get_installation()

    if not installation:
        return {}

    entitlement_meta = frappe.get_meta(
        "Vuma Installation Module"
    )

    fields = [
        "name",
        "module",
        "licensed_from",
        "licensed_until",
        "user_limit",
        "pos_limit",
        "company_limit",
        "location_limit",
    ]

    if entitlement_meta.has_field("employee_limit"):
        fields.append("employee_limit")

    rows = frappe.get_all(
        "Vuma Installation Module",
        filters={
            "installation": installation.name,
            "enabled": 1,
        },
        fields=fields,
        limit_page_length=100,
    )

    result = {}

    for row in rows:
        module = frappe.db.get_value(
            "Vuma Module",
            row.module,
            [
                "module_code",
                "module_name",
                "category",
                "active",
                "requires_user_count",
                "requires_pos_count",
                "requires_company_count",
                "requires_location_count",
                "requires_employee_count",
            ],
            as_dict=True,
        )

        if not module:
            continue

        if not module.active:
            continue

        code = (
            module.module_code or ""
        ).strip().upper()

        if not code:
            continue

        result[code] = {
            "code": code,
            "name": module.module_name,
            "category": module.category,

            "entitlement": row.name,

            "licensed_from": row.licensed_from,
            "licensed_until": row.licensed_until,

            "user_limit":
                row.get("user_limit") or 0,

            "pos_limit":
                row.get("pos_limit") or 0,

            "company_limit":
                row.get("company_limit") or 0,

            "location_limit":
                row.get("location_limit") or 0,

            "employee_limit":
                row.get("employee_limit") or 0,

            "requires_user_count":
                bool(module.requires_user_count),

            "requires_pos_count":
                bool(module.requires_pos_count),

            "requires_company_count":
                bool(module.requires_company_count),

            "requires_location_count":
                bool(module.requires_location_count),

            "requires_employee_count":
                bool(module.requires_employee_count),
        }

    return result


def get_enabled_module_codes():
    return sorted(get_enabled_entitlements().keys())


def is_module_enabled(module_code):
    if not module_code:
        return False

    code = str(module_code).strip().upper()

    return code in get_enabled_entitlements()


def assert_module_enabled(module_code):
    """
    Server-side licence gate.

    Call this at the beginning of protected Vuma endpoints/actions.
    """

    code = str(module_code or "").strip().upper()

    if not code:
        frappe.throw(
            _("A Vuma module code is required."),
            exc=VumaEntitlementError,
        )

    if not is_module_enabled(code):
        module_name = frappe.db.get_value(
            "Vuma Module",
            {"module_code": code},
            "module_name",
        )

        frappe.throw(
            _(
                "{0} is not licensed for this Vuma installation."
            ).format(module_name or code),
            exc=VumaEntitlementError,
        )

    return True


def get_module_entitlement(module_code):
    code = str(module_code or "").strip().upper()

    entitlements = get_enabled_entitlements()

    entitlement = entitlements.get(code)

    if not entitlement:
        return None

    return entitlement


@frappe.whitelist()
def get_client_entitlements():
    """
    Safe licence data for the Desk UI.

    Do not expose signing secrets, tokens, private keys or
    Control credentials here.
    """

    installation = get_installation()
    entitlements = get_enabled_entitlements()

    if not installation:
        return {
            "configured": False,
            "modules": [],
            "entitlements": {},
        }

    return {
        "configured": True,

        "installation": {
            "id": installation.installation_id,
            "name": installation.installation_name,
            "customer": installation.customer_name,
            "licence_status": installation.licence_status,
            "licence_valid_from": installation.licence_valid_from,
            "licence_valid_until": installation.licence_valid_until,
            "grace_until": installation.grace_until,
            "integrity_status": installation.integrity_status,
        },

        "modules": sorted(entitlements.keys()),

        "entitlements": entitlements,
    }
