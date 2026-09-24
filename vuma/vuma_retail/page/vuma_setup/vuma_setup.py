import json
import uuid

import frappe
from frappe import _
from frappe.utils import today


@frappe.whitelist()
def complete_setup(payload):
    if isinstance(payload, str):
        payload = json.loads(payload)

    if not isinstance(payload, dict):
        frappe.throw(_("Invalid setup payload."))

    installation_data = payload.get("installation") or {}
    companies_data = payload.get("companies") or []
    locations_data = payload.get("locations") or []
    mappings_data = payload.get("mappings") or []
    modules_data = payload.get("modules") or []
    limits_data = payload.get("limits") or {}

    validate_setup(
        installation_data,
        companies_data,
        locations_data,
        mappings_data,
        modules_data,
        limits_data,
    )

    installation_id = (
        installation_data.get("installation_id") or ""
    ).strip()

    if not installation_id:
        installation_id = (
            f"VUMA-LOCAL-{uuid.uuid4().hex[:8].upper()}"
        )

    if frappe.db.exists(
        "Vuma Installation",
        {"installation_id": installation_id},
    ):
        frappe.throw(
            _("Installation ID {0} already exists.").format(
                installation_id
            )
        )

    installation = frappe.get_doc(
        {
            "doctype": "Vuma Installation",
            "installation_id": installation_id,
            "installation_name": installation_data["installation_name"],
            "customer_name": installation_data["customer_name"],
            "company_count": installation_data["company_count"],
            "location_count": installation_data["location_count"],
            "licensed_user_count": installation_data["licensed_user_count"],
            "licensed_pos_count": installation_data.get(
                "licensed_pos_count", 0
            ),
            "setup_complete": 0,
            "licence_status": "Pending",
            "integrity_status": "Unknown",
        }
    )

    installation.insert(ignore_permissions=False)

    company_names = []

    for company_data in companies_data:
        company_name = company_data["company_name"].strip()

        existing_company = frappe.db.exists(
            "Company",
            {"company_name": company_name},
        )

        if existing_company:
            company = frappe.get_doc(
                "Company",
                existing_company,
            )

            company.update(
                {
                    "company_registration_no": (
                        company_data.get("company_registration_no") or ""
                    ).strip(),
                    "is_vat_registered": int(
                        company_data.get("is_vat_registered") or 0
                    ),
                    "tax_id": (company_data.get("tax_id") or "").strip(),
                    "company_logo": company_data.get("company_logo") or None,
                }
            )

            company.save(ignore_permissions=False)
        else:
            company = frappe.get_doc(
                {
                    "doctype": "Company",
                    "company_name": company_name,
                    "abbr": company_data["abbr"].strip().upper(),
                    "country": company_data["country"],
                    "default_currency": company_data["default_currency"],
                    "company_registration_no": (
                        company_data.get("company_registration_no") or ""
                    ).strip(),
                    "is_vat_registered": int(
                        company_data.get("is_vat_registered") or 0
                    ),
                    "tax_id": (company_data.get("tax_id") or "").strip(),
                    "company_logo": company_data.get("company_logo") or None,
                }
            )

            company.insert(ignore_permissions=False)

        company_names.append(company.name)

    location_names = []

    for location_data in locations_data:
        location_code = (
            location_data["location_code"]
            .strip()
            .upper()
        )

        if frappe.db.exists(
            "Vuma Location",
            {"location_code": location_code},
        ):
            frappe.throw(
                _("Location code {0} already exists.").format(
                    location_code
                )
            )

        location = frappe.get_doc(
            {
                "doctype": "Vuma Location",
                "location_name": location_data["location_name"],
                "location_code": location_code,
                "active": 1,
                "address_line_1": location_data.get("address_line_1"),
                "address_line_2": location_data.get("address_line_2"),
                "city": location_data.get("city"),
                "province": location_data.get("province"),
                "postal_code": location_data.get("postal_code"),
                "country": location_data.get("country"),
                "phone": location_data.get("phone"),
                "email": location_data.get("email"),
                "is_head_office": int(
                    location_data.get("is_head_office", 0)
                ),
                "allow_pos": int(
                    location_data.get("allow_pos", 0)
                ),
                "allow_stock": int(
                    location_data.get("allow_stock", 0)
                ),
                "allow_deliveries": int(
                    location_data.get("allow_deliveries", 0)
                ),
            }
        )

        location.insert(ignore_permissions=False)

        location_names.append(location.name)

    for mapping in mappings_data:
        company_index = int(mapping["company_index"])
        location_index = int(mapping["location_index"])

        company_name = company_names[company_index]
        location_name = location_names[location_index]

        if not frappe.db.exists(
            "Vuma Company Location",
            {
                "company": company_name,
                "location": location_name,
            },
        ):
            mapping_doc = frappe.get_doc(
                {
                    "doctype": "Vuma Company Location",
                    "company": company_name,
                    "location": location_name,
                    "active": 1,
                }
            )

            mapping_doc.insert(ignore_permissions=False)

    installation_module_meta = frappe.get_meta(
        "Vuma Installation Module"
    )

    for module_data in modules_data:
        module_code = (
            module_data["module_code"]
            .strip()
            .upper()
        )

        module_name = frappe.db.get_value(
            "Vuma Module",
            {
                "module_code": module_code,
                "active": 1,
            },
            "name",
        )

        if not module_name:
            frappe.throw(
                _("Active Vuma module {0} was not found.").format(
                    module_code
                )
            )

        module_limits = limits_data.get(module_code) or {}

        entitlement = {
            "doctype": "Vuma Installation Module",
            "installation": installation.name,
            "module": module_name,
            "enabled": 1,
            "licensed_from": today(),
            "user_limit": int(
                module_limits.get("user_limit", 0) or 0
            ),
            "pos_limit": int(
                module_limits.get("pos_limit", 0) or 0
            ),
            "company_limit": int(
                module_limits.get("company_limit", 0) or 0
            ),
            "location_limit": int(
                module_limits.get("location_limit", 0) or 0
            ),
        }

        if installation_module_meta.has_field("employee_limit"):
            entitlement["employee_limit"] = int(
                module_limits.get("employee_limit", 0) or 0
            )

        frappe.get_doc(entitlement).insert(
            ignore_permissions=False
        )

    installation.setup_complete = 1
    installation.save(ignore_permissions=False)

    return {
        "installation": installation.name,
        "installation_id": installation_id,
        "companies": company_names,
        "locations": location_names,
        "modules": len(modules_data),
    }


def validate_setup(
    installation,
    companies,
    locations,
    mappings,
    modules,
    limits,
):
    required_installation_fields = (
        "installation_name",
        "customer_name",
        "company_count",
        "location_count",
        "licensed_user_count",
    )

    for field in required_installation_fields:
        if not installation.get(field):
            frappe.throw(
                _("Installation field {0} is required.").format(
                    field
                )
            )

    company_count = int(
        installation["company_count"]
    )

    location_count = int(
        installation["location_count"]
    )

    licensed_user_count = int(
        installation["licensed_user_count"]
    )

    licensed_pos_count = int(
        installation.get("licensed_pos_count", 0)
        or 0
    )

    if company_count < 1:
        frappe.throw(
            _("At least one company is required.")
        )

    if location_count < 1:
        frappe.throw(
            _("At least one location is required.")
        )

    if licensed_user_count < 1:
        frappe.throw(
            _("At least one licensed user is required.")
        )

    if licensed_pos_count < 0:
        frappe.throw(
            _("POS limit cannot be negative.")
        )

    if len(companies) != company_count:
        frappe.throw(
            _(
                "Company count does not match the installation licence."
            )
        )

    if len(locations) != location_count:
        frappe.throw(
            _(
                "Location count does not match the installation licence."
            )
        )

    if not mappings:
        frappe.throw(
            _(
                "At least one company/location mapping is required."
            )
        )

    if not modules:
        frappe.throw(
            _("At least one module must be licensed.")
        )

    company_names = set()

    for company in companies:
        name = (
            company.get("company_name") or ""
        ).strip()

        abbr = (
            company.get("abbr") or ""
        ).strip()

        if not name:
            frappe.throw(
                _("Every company requires a name.")
            )

        if not abbr:
            frappe.throw(
                _(
                    "Every company requires an abbreviation."
                )
            )

        lowered = name.lower()

        if lowered in company_names:
            frappe.throw(
                _("Duplicate company name: {0}").format(
                    name
                )
            )

        company_names.add(lowered)

    location_codes = set()

    for location in locations:
        name = (
            location.get("location_name") or ""
        ).strip()

        code = (
            location.get("location_code") or ""
        ).strip().upper()

        if not name:
            frappe.throw(
                _(
                    "Every location requires a name."
                )
            )

        if not code:
            frappe.throw(
                _(
                    "Every location requires a code."
                )
            )

        if code in location_codes:
            frappe.throw(
                _("Duplicate location code: {0}").format(
                    code
                )
            )

        location_codes.add(code)

    mapped_companies = set()
    mapped_locations = set()

    for mapping in mappings:
        company_index = int(
            mapping["company_index"]
        )

        location_index = int(
            mapping["location_index"]
        )

        if not 0 <= company_index < len(companies):
            frappe.throw(
                _("Invalid company mapping.")
            )

        if not 0 <= location_index < len(locations):
            frappe.throw(
                _("Invalid location mapping.")
            )

        mapped_companies.add(company_index)
        mapped_locations.add(location_index)

    if len(mapped_companies) != len(companies):
        frappe.throw(
            _(
                "Every company must have at least one location."
            )
        )

    if len(mapped_locations) != len(locations):
        frappe.throw(
            _(
                "Every location must belong to at least one company."
            )
        )

    module_codes = set()

    for module in modules:
        code = (
            module.get("module_code") or ""
        ).strip().upper()

        if not code:
            frappe.throw(
                _("Invalid module selection.")
            )

        if code in module_codes:
            frappe.throw(
                _("Duplicate module: {0}").format(
                    code
                )
            )

        module_codes.add(code)

        module_limit = limits.get(code) or {}

        user_limit = int(
            module_limit.get("user_limit", 0)
            or 0
        )

        pos_limit = int(
            module_limit.get("pos_limit", 0)
            or 0
        )

        company_limit = int(
            module_limit.get("company_limit", 0)
            or 0
        )

        location_limit = int(
            module_limit.get("location_limit", 0)
            or 0
        )

        employee_limit = int(
            module_limit.get("employee_limit", 0)
            or 0
        )

        if user_limit > licensed_user_count:
            frappe.throw(
                _(
                    "{0}: module user limit exceeds installation limit."
                ).format(code)
            )

        if pos_limit > licensed_pos_count:
            frappe.throw(
                _(
                    "{0}: module POS limit exceeds installation limit."
                ).format(code)
            )

        if company_limit > company_count:
            frappe.throw(
                _(
                    "{0}: module company limit exceeds installation limit."
                ).format(code)
            )

        if location_limit > location_count:
            frappe.throw(
                _(
                    "{0}: module location limit exceeds installation limit."
                ).format(code)
            )

        if employee_limit < 0:
            frappe.throw(
                _(
                    "{0}: employee limit cannot be negative."
                ).format(code)
            )
