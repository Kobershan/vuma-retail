
from __future__ import annotations

import frappe
from frappe import _

from vuma.api.v1.responses import success
from vuma.licensing.entitlements import (
    assert_module_enabled,
    get_enabled_module_codes,
)


MODULE_REGISTRY = { 'ACC': {'name': 'Accounting & Finance',
         'screens': {'Dashboard': None,
                     'Chart of Accounts': 'Account',
                     'General Ledger': 'GL Entry',
                     'Journal Entries': 'Journal Entry',
                     'Journal Templates': 'Journal Entry Template',
                     'Accounts Receivable': 'Sales Invoice',
                     'Accounts Payable': 'Purchase Invoice',
                     'Payments': 'Payment Entry',
                     'Payment Terms': 'Payment Terms Template',
                     'Banking': 'Bank Account',
                     'Bank Transactions': 'Bank Transaction',
                     'Bank Clearance': 'Bank Clearance',
                     'Budgets': 'Budget',
                     'Cost Centres': 'Cost Center',
                     'Tax Categories': 'Tax Category',
                     'Tax Rules': 'Tax Rule',
                     'Item Tax Templates': 'Item Tax Template',
                     'Modes of Payment': 'Mode of Payment',
                     'Currency Exchange': 'Currency Exchange',
                     'Fiscal Years': 'Fiscal Year',
                     'Accounting Periods': 'Accounting Period',
                     'Period Closing': 'Period Closing Voucher',
                     'Finance Books': 'Finance Book',
                     'Subscriptions': 'Subscription',
                     'Subscription Plans': 'Subscription Plan',
                     'Dunning': 'Dunning',
                     'Financial Reports': None}},
 'SAL': {'name': 'Sales',
         'screens': {'Dashboard': None,
                     'Customers': 'Customer',
                     'Customer Groups': 'Customer Group',
                     'Territories': 'Territory',
                     'Sales Persons': 'Sales Person',
                     'Sales Partners': 'Sales Partner',
                     'Quotations': 'Quotation',
                     'Sales Orders': 'Sales Order',
                     'Picking': None,
                     'Delivery Notes': 'Delivery Note',
                     'Sales Invoices': 'Sales Invoice',
                     'Returns': 'Sales Invoice',
                     'Installation Notes': 'Installation Note',
                     'Product Bundles': 'Product Bundle',
                     'Blanket Orders': 'Blanket Order',
                     'Sales Forecasts': 'Sales Forecast',
                     'Pricing': 'Pricing Rule',
                     'Sales Reports': None}},
 'PUR': {'name': 'Purchasing',
         'screens': {'Dashboard': None,
                     'Bulk Receive': None,
                     'Suppliers': 'Supplier',
                     'Supplier Groups': 'Supplier Group',
                     'Supplier Scorecards': 'Supplier Scorecard',
                     'Material Requests': 'Material Request',
                     'Requests for Quotation': 'Request for Quotation',
                     'Supplier Quotations': 'Supplier Quotation',
                     'Purchase Orders': 'Purchase Order',
                     'Goods Received': 'Purchase Receipt',
                     'Purchase Invoices': 'Purchase Invoice',
                     'Purchase Returns': 'Purchase Receipt',
                     'Buying Settings': 'Buying Settings'}},
 'INV': {'name': 'Inventory',
         'screens': {'Dashboard': None,
                     'Items': 'Item',
                     'Item Groups': 'Item Group',
                     'Item Attributes': 'Item Attribute',
                     'Item Prices': 'Item Price',
                     'Price Lists': 'Price List',
                     'Manufacturers': 'Manufacturer',
                     'Stock Levels': 'Bin',
                     'Stock Ledger': 'Stock Ledger Entry',
                     'Warehouses': 'Warehouse',
                     'Warehouse Types': 'Warehouse Type',
                     'Batches': 'Batch',
                     'Serial Numbers': 'Serial No',
                     'Stock Transfers': 'Stock Entry',
                     'Stock Counts': 'Stock Reconciliation',
                     'Pick Lists': 'Pick List',
                     'Packing Slips': 'Packing Slip',
                     'Shipments': 'Shipment',
                     'Delivery Trips': 'Delivery Trip',
                     'Landed Cost Vouchers': 'Landed Cost Voucher',
                     'Quality Inspections': 'Quality Inspection',
                     'Replenishment': 'Material Request',
                     'UOMs': 'UOM',
                     'UOM Categories': 'UOM Category',
                     'Stock Settings': 'Stock Settings',
                     'Inventory Reports': None}},
 'POS': {'name': 'Point of Sale',
         'screens': {'Open POS': 'POS Invoice',
                     'POS Profiles': 'POS Profile',
                     'Registers': 'POS Opening Entry',
                     'Shifts': 'POS Closing Entry',
                     'Cashier Closings': 'Cashier Closing',
                     'Cash Management': 'Payment Entry',
                     'Transactions': 'POS Invoice',
                     'Returns': 'POS Invoice',
                     'Terminal Management': 'Vuma Device'}},
 'MFG': {'name': 'Manufacturing',
         'screens': {'Dashboard': None,
                     'Bills of Materials': 'BOM',
                     'BOM Creator': 'BOM Creator',
                     'Routings': 'Routing',
                     'Operations': 'Operation',
                     'Workstations': 'Workstation',
                     'Workstation Types': 'Workstation Type',
                     'Work Orders': 'Work Order',
                     'Production Planning': 'Production Plan',
                     'Job Cards': 'Job Card',
                     'Downtime Entries': 'Downtime Entry',
                     'Material Consumption': 'Stock Entry',
                     'Subcontracting Orders': 'Subcontracting Order',
                     'Subcontracting Receipts': 'Subcontracting Receipt',
                     'Production Reports': None}},
 'SRV': {'name': 'Services',
         'screens': {'Service Dashboard': None,
                     'Issues': 'Issue',
                     'Issue Types': 'Issue Type',
                     'Warranty Claims': 'Warranty Claim',
                     'Service Level Agreements': 'Service Level Agreement',
                     'Service Orders': None,
                     'Jobs': None,
                     'Appointments': 'Appointment',
                     'Technicians': None,
                     'Service Items': 'Item',
                     'Service Reports': None}},
 'PRJ': {'name': 'Projects',
         'screens': {'Projects': 'Project',
                     'Project Templates': 'Project Template',
                     'Project Types': 'Project Type',
                     'Tasks': 'Task',
                     'Activity Types': 'Activity Type',
                     'Timesheets': 'Timesheet',
                     'Project Updates': 'Project Update',
                     'Milestones': None,
                     'Project Costing': None,
                     'Project Reports': None}},
 'AST': {'name': 'Assets',
         'screens': {'Assets': 'Asset',
                     'Asset Categories': 'Asset Category',
                     'Locations': 'Location',
                     'Depreciation': None,
                     'Depreciation Schedules': 'Asset Depreciation Schedule',
                     'Asset Movement': 'Asset Movement',
                     'Asset Maintenance': 'Asset Maintenance',
                     'Asset Repairs': 'Asset Repair',
                     'Asset Capitalization': 'Asset Capitalization',
                     'Asset Shift Allocations': 'Asset Shift Allocation',
                     'Asset Reports': None}},
 'CRM': {'name': 'CRM',
         'screens': {'Dashboard': None,
                     'Leads': 'Lead',
                     'Opportunities': 'Opportunity',
                     'Opportunity Types': 'Opportunity Type',
                     'Customers': 'Customer',
                     'Prospects': 'Prospect',
                     'Contacts': 'Contact',
                     'Campaigns': 'Campaign',
                     'Contracts': 'Contract',
                     'Competitors': 'Competitor',
                     'Market Segments': 'Market Segment',
                     'Sales Stages': 'Sales Stage',
                     'Appointments': 'Appointment',
                     'Activities': 'ToDo',
                     'Sales Pipeline': None}},
 'HRP': {'name': 'HR & Payroll',
         'screens': {'Employees': 'Employee',
                     'Branches': 'Branch',
                     'Departments': 'Department',
                     'Designations': 'Designation',
                     'Holiday Lists': 'Holiday List',
                     'Attendance': 'Attendance',
                     'Leave': 'Leave Application',
                     'Shifts': 'Shift Assignment',
                     'Payroll': 'Salary Slip',
                     'Expenses': 'Expense Claim',
                     'Performance': 'Appraisal',
                     'Drivers': 'Driver',
                     'Vehicles': 'Vehicle',
                     'HR Reports': None}},
 'QMS': {'name': 'Quality Management',
         'screens': {'Quality Inspections': 'Quality Inspection',
                     'Quality Goals': 'Quality Goal',
                     'Quality Reviews': 'Quality Review',
                     'Quality Procedures': 'Quality Procedure',
                     'Quality Feedback': 'Quality Feedback',
                     'Non-Conformance': 'Non Conformance',
                     'Corrective Actions': 'Quality Action',
                     'Quality Reports': None}},
 'MNT': {'name': 'Maintenance',
         'screens': {'Maintenance Schedule': 'Maintenance Schedule',
                     'Maintenance Visits': 'Maintenance Visit',
                     'Equipment': 'Asset',
                     'Preventive Maintenance': 'Asset Maintenance',
                     'Breakdowns': None,
                     'Maintenance Reports': None}},
 'ECM': {'name': 'E-commerce',
         'screens': {'Storefront': None,
                     'Products': 'Item',
                     'Website Item Groups': 'Website Item Group',
                     'Online Orders': 'Sales Order',
                     'Customers': 'Customer',
                     'Payments': 'Payment Entry',
                     'Fulfilment': 'Delivery Note',
                     'Store Settings': None}},
 'LOY': {'name': 'Loyalty',
         'screens': {'Loyalty Programs': 'Loyalty Program',
                     'Loyalty Point Entries': 'Loyalty Point Entry',
                     'Members': None,
                     'Points': None,
                     'Rewards': None,
                     'Tiers': None,
                     'Campaigns': None,
                     'Transactions': None,
                     'Loyalty Reports': None}},
 'SUP': {'name': 'Supplier Connect',
         'screens': {'Supplier Network': 'Supplier',
                     'Supplier Groups': 'Supplier Group',
                     'Supplier Catalogue': None,
                     'Orders': None,
                     'Messages': None,
                     'Documents': None,
                     'Performance': None}},
 'MOB': {'name': 'Mobile Management',
         'screens': {'Mobile Dashboard': None,
                     'Registered Devices': 'Vuma Device',
                     'Managers': None,
                     'Drivers': 'Driver',
                     'Vehicles': 'Vehicle',
                     'Proof of Delivery': None,
                     'Mobile Activity': None}},
 'MCO': {'name': 'Multi-Company',
         'screens': {'Companies': 'Company',
                     'Locations': 'Vuma Location',
                     'Company Groups': None,
                     'Intercompany': None,
                     'Consolidation': None}},
 'RPT': {'name': 'Advanced Reporting',
         'screens': {'Dashboards': None,
                     'Reports': None,
                     'Analytics': None,
                     'KPIs': None,
                     'Exports': None,
                     'Scheduled Reports': None}},
 'API': {'name': 'API & Integrations',
         'screens': {'API Access': None,
                     'Integrations': None,
                     'Webhooks': 'Webhook',
                     'API Keys': None,
                     'Sync Status': None,
                     'Integration Logs': 'Integration Request'}},
 'AUD': {'name': 'Audit & Compliance',
         'screens': {'Audit Trail': 'Version',
                     'User Activity': 'Activity Log',
                     'Approvals': 'Workflow Action',
                     'Exceptions': None,
                     'Compliance': None,
                     'Audit Reports': None}}}


CANDIDATE_FIELDS = [
    "name",
    "title",
    "subject",
    "customer",
    "customer_name",
    "supplier",
    "supplier_name",
    "company",
    "item_code",
    "item_name",
    "item_group",
    "warehouse",
    "status",
    "docstatus",
    "posting_date",
    "transaction_date",
    "due_date",
    "delivery_date",
    "grand_total",
    "rounded_total",
    "outstanding_amount",
    "currency",
    "tax_id",
    "company_registration_no",
    "expiry_date",
    "manufacturing_date",
    "shelf_life_in_days",
    "warranty_expiry_date",
    "disabled",
    "enabled",
    "creation",
    "modified",
]


class VumaModuleError(frappe.ValidationError):
    pass


def _module(module_code):
    module_code = str(module_code or "").strip().upper()

    if module_code not in MODULE_REGISTRY:
        frappe.throw(
            _("Unknown Vuma module."),
            exc=VumaModuleError,
        )

    assert_module_enabled(module_code)

    return module_code, MODULE_REGISTRY[module_code]


def _screen(module_code, screen):
    module_code, module = _module(module_code)
    screen = str(screen or "").strip()
    screens = module["screens"]

    if screen not in screens:
        frappe.throw(
            _("Unknown Vuma screen."),
            exc=VumaModuleError,
        )

    return module_code, module, screen, screens[screen]


def _doctype_exists(doctype):
    return bool(
        doctype
        and frappe.db.exists(
            "DocType",
            doctype,
        )
    )


def _fields_for(doctype):
    meta = frappe.get_meta(doctype)
    fields = ["name"]

    for fieldname in CANDIDATE_FIELDS:
        if (
            fieldname != "name"
            and meta.has_field(fieldname)
        ):
            fields.append(fieldname)

    return list(dict.fromkeys(fields))


def _search_fields(doctype):
    meta = frappe.get_meta(doctype)

    candidates = [
        "name",
        "title",
        "subject",
        "customer",
        "customer_name",
        "supplier",
        "supplier_name",
        "item_code",
        "item_name",
    ]

    result = []

    for fieldname in candidates:
        if (
            fieldname == "name"
            or meta.has_field(fieldname)
        ):
            result.append(fieldname)

    return result


@frappe.whitelist()
def catalog():
    enabled = set(
        get_enabled_module_codes()
    )

    items = []

    for code, module in MODULE_REGISTRY.items():
        if code not in enabled:
            continue

        screens = []

        for screen_name, doctype in module["screens"].items():
            screens.append({
                "name": screen_name,
                "doctype": doctype,
                "kind": (
                    "doctype"
                    if doctype
                    else "custom"
                ),
                "available": (
                    _doctype_exists(doctype)
                    if doctype
                    else True
                ),
            })

        items.append({
            "code": code,
            "name": module["name"],
            "screens": screens,
        })

    return success(
        data={
            "modules": items,
        }
    )


@frappe.whitelist()
def dashboard(module_code, company=None):
    module_code, module = _module(module_code)
    company = _validated_company(company)

    metrics = []
    seen = set()

    for screen_name, doctype in module["screens"].items():
        if not doctype or doctype in seen:
            continue

        seen.add(doctype)

        if not _doctype_exists(doctype):
            metrics.append({
                "label": screen_name,
                "doctype": doctype,
                "count": None,
                "available": False,
            })
            continue

        try:
            filters = _company_filters(doctype, company)
            count = frappe.db.count(doctype, filters=filters or None)

            metrics.append({
                "label": screen_name,
                "doctype": doctype,
                "count": int(count or 0),
                "available": True,
            })
        except Exception:
            metrics.append({
                "label": screen_name,
                "doctype": doctype,
                "count": None,
                "available": False,
            })

        if len(metrics) >= 8:
            break

    return success(
        data={
            "module_code": module_code,
            "module_name": module["name"],
            "metrics": metrics,
        }
    )


def _validated_company(company):
    company = str(company or "").strip()

    if not company:
        return None

    if not frappe.db.exists("Company", company):
        return None

    return company


def _company_filters(doctype, company):
    if not company:
        return {}

    try:
        if frappe.get_meta(doctype).has_field("company"):
            return {"company": company}
    except Exception:
        pass

    return {}


@frappe.whitelist()
def screen(
    module_code,
    screen,
    search=None,
    limit=50,
    start=0,
    company=None,
):
    (
        module_code,
        module,
        screen_name,
        doctype,
    ) = _screen(
        module_code,
        screen,
    )

    if not doctype:
        metrics = []
        seen = set()
        for sname, sdoctype in module["screens"].items():
            if not sdoctype or sdoctype in seen:
                continue
            seen.add(sdoctype)
            if _doctype_exists(sdoctype):
                try:
                    count = frappe.db.count(sdoctype)
                    metrics.append({
                        "label": sname,
                        "doctype": sdoctype,
                        "count": int(count or 0),
                        "available": True,
                    })
                except Exception:
                    pass
            if len(metrics) >= 8:
                break

        return success(
            data={
                "module_code": module_code,
                "module_name": module["name"],
                "screen": screen_name,
                "kind": "custom",
                "implemented": True,
                "available": True,
                "doctype": None,
                "items": metrics,
                "columns": [
                    {"fieldname": "label", "label": "Section"},
                    {"fieldname": "doctype", "label": "Doctype"},
                    {"fieldname": "count", "label": "Count"},
                ],
                "message": "Module overview",
            }
        )

    if not _doctype_exists(doctype):
        return success(
            data={
                "module_code": module_code,
                "module_name": module["name"],
                "screen": screen_name,
                "kind": "doctype",
                "doctype": doctype,
                "implemented": True,
                "available": False,
                "items": [],
                "columns": [],
                "message": (
                    f"{doctype} is not installed "
                    "on this VUMA site."
                ),
            }
        )

    limit = min(max(int(limit), 1), 200)
    start = max(int(start), 0)

    fields = _fields_for(doctype)

    or_filters = None

    if search:
        search = str(search).strip()

        if search:
            or_filters = {
                fieldname: [
                    "like",
                    f"%{search}%",
                ]
                for fieldname in _search_fields(doctype)
            }

    rows = frappe.get_list(
        doctype,
        fields=fields,
        filters=_company_filters(doctype, _validated_company(company)),
        or_filters=or_filters,
        order_by="modified desc",
        start=start,
        page_length=limit,
    )

    meta = frappe.get_meta(doctype)

    columns = [
        {
            "fieldname": fieldname,
            "label": (
                meta.get_label(fieldname)
                or fieldname
            ),
        }
        for fieldname in fields
    ]

    return success(
        data={
            "module_code": module_code,
            "module_name": module["name"],
            "screen": screen_name,
            "kind": "doctype",
            "doctype": doctype,
            "implemented": True,
            "available": True,
            "columns": columns,
            "items": rows,
            "start": start,
            "limit": limit,
        }
    )


NON_INPUT_FIELDTYPES = {
    "Section Break",
    "Column Break",
    "Tab Break",
    "HTML",
    "HTML Editor",
    "Heading",
    "Image",
    "Button",
    "Fold",
    "Geolocation",
    "Signature",
    "Separator",
}

SYSTEM_FIELDNAMES = {
    "name",
    "owner",
    "creation",
    "modified",
    "modified_by",
    "docstatus",
    "idx",
    "doctype",
    "parent",
    "parentfield",
    "parenttype",
}

COMMON_CHILD_FIELDS = {
    "item_code",
    "item_name",
    "description",
    "qty",
    "rate",
    "amount",
    "uom",
    "warehouse",
    "batch_no",
    "delivery_date",
    "against_sales_order",
    "against_sales_invoice",
    "income_account",
    "expense_account",
    "cost_center",
}


def _describe_field(df):
    return {
        "fieldname": df.fieldname,
        "label": df.label or df.fieldname,
        "fieldtype": df.fieldtype,
        "reqd": bool(df.reqd),
        "options": df.options,
        "default": df.default,
        "read_only": bool(df.read_only),
        "hidden": bool(df.hidden),
        "in_list_view": bool(df.in_list_view),
        "length": df.length or None,
    }


def _describe_fields(meta, child=False):
    fields = []

    for df in meta.fields:
        if not df.fieldname:
            continue

        if df.fieldtype in NON_INPUT_FIELDTYPES:
            continue

        if df.fieldname in SYSTEM_FIELDNAMES:
            continue

        if df.fieldtype == "Table":
            continue

        if df.hidden and not df.reqd:
            continue

        if child and not (
            df.reqd
            or df.in_list_view
            or df.fieldname in COMMON_CHILD_FIELDS
        ):
            continue

        fields.append(_describe_field(df))

    fields.sort(key=lambda f: (not f["reqd"],))

    return fields


@frappe.whitelist()
def describe(doctype: str):
    if not _doctype_exists(doctype):
        frappe.throw(
            _("Doctype {0} not found.").format(doctype),
            exc=VumaModuleError,
        )

    meta = frappe.get_meta(doctype)

    tables = []

    for df in meta.fields:
        if df.fieldtype != "Table" or not df.options:
            continue

        if df.hidden:
            continue

        if not _doctype_exists(df.options):
            continue

        child_meta = frappe.get_meta(df.options)

        tables.append({
            "fieldname": df.fieldname,
            "label": df.label or df.fieldname,
            "reqd": bool(df.reqd),
            "child_doctype": df.options,
            "fields": _describe_fields(
                child_meta,
                child=True,
            ),
        })

    autoname = (meta.autoname or "").strip()

    return success(
        data={
            "doctype": meta.name,
            "title": meta.name,
            "name_autogenerated": bool(
                autoname and autoname != "Prompt"
            ),
            "fields": _describe_fields(meta),
            "tables": tables,
        }
    )


@frappe.whitelist()
def create_doc(doctype: str, data=None):
    # data may arrive as a JSON string over GET; normalize first so
    # Desk callers (native dict) and the web client both work.
    data = frappe.parse_json(data or {})
    module_code = str(data.get("module_code", "")).strip().upper() if data else ""
    _module(module_code)
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)
    values = dict(data or {})
    values.pop("module_code", None)
    doc = frappe.new_doc(doctype, values)
    doc.insert()
    return success(data={"name": doc.name, "doctype": doctype, "docstatus": doc.docstatus})


@frappe.whitelist()
def get_doc(doctype: str, name: str):
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)
    doc = frappe.get_doc(doctype, name)
    return success(data=doc.as_dict())


@frappe.whitelist()
def save_doc(doctype: str, name: str, data=None):
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)
    data = frappe.parse_json(data or {})
    doc = frappe.get_doc(doctype, name)
    doc.update(data)
    doc.save()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def submit_doc(doctype: str, name: str):
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)
    doc = frappe.get_doc(doctype, name)
    doc.submit()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def cancel_doc(doctype: str, name: str):
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)
    doc = frappe.get_doc(doctype, name)
    doc.cancel()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def delete_doc(doctype: str, name: str):
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)
    doc = frappe.get_doc(doctype, name)
    doc.delete()
    return success(data={"name": doc.name, "deleted": True})


REVERSIBLE_DOCTYPES = {
    "Sales Invoice",
    "POS Invoice",
    "Purchase Invoice",
    "Delivery Note",
    "Purchase Receipt",
    "Journal Entry",
}


@frappe.whitelist()
def reverse_doc(doctype: str, name: str):
    if not _doctype_exists(doctype):
        frappe.throw(_("Doctype {0} not found.").format(doctype), exc=VumaModuleError)

    if doctype not in REVERSIBLE_DOCTYPES:
        frappe.throw(
            _("{} cannot be reversed.").format(doctype),
            exc=VumaModuleError,
        )

    doc = frappe.get_doc(doctype, name)

    if doc.docstatus != 1:
        frappe.throw(
            _("Only submitted documents can be reversed. Delete the draft instead."),
            exc=VumaModuleError,
        )

    if doctype == "Journal Entry":
        from erpnext.accounts.doctype.journal_entry.journal_entry import (
            make_reverse_journal_entry,
        )

        reversal = make_reverse_journal_entry(name)
    else:
        from erpnext.controllers.sales_and_purchase_return import (
            make_return_doc,
        )

        reversal = make_return_doc(doctype, name)

    reversal.insert()
    reversal.submit()

    return success(
        data={
            "name": reversal.name,
            "doctype": doctype,
            "docstatus": reversal.docstatus,
            "return_against": name,
        }
    )
