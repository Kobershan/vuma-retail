import datetime

import frappe
from frappe import _

from vuma.api.v1.responses import success
from vuma.licensing.entitlements import assert_module_enabled


class VumaBulkError(frappe.ValidationError):
    pass


def _leaf_group(doctype, fallback):
    rows = frappe.get_all(
        doctype, filters={"is_group": 0}, limit=5
    )

    if rows:
        return rows[0].name

    return fallback


def _resolve_bulk_item(code, item_name=None):
    """Find an item by barcode, code or name. Returns item name or None."""
    code = str(code or "").strip()

    if not code:
        return None

    barcode = frappe.db.get_value(
        "Item Barcode", {"barcode": code}, "parent"
    )

    if barcode and frappe.db.exists("Item", barcode):
        return barcode

    if frappe.db.exists("Item", code):
        return code

    found = frappe.db.get_value(
        "Item", {"item_name": code}, "name"
    )

    if found:
        return found

    if item_name:
        found = frappe.db.get_value(
            "Item", {"item_name": item_name}, "name"
        )

        if found:
            return found

    return None


def _ensure_bulk_item(code, item_name, company, warehouse=None, track_expiry=True):
    """Get or create a batch-tracked stock item for bulk receiving.

    track_expiry=False for products with no printed date (batch-tracked
    without expiry). Expiry-tracked items always require a date.
    """
    found = _resolve_bulk_item(code, item_name)

    if found:
        item = frappe.get_doc("Item", found)

        if not item.get("has_batch_no"):
            if frappe.db.count(
                "Stock Ledger Entry", {"item_code": item.name}
            ):
                frappe.throw(
                    _("{} already has stock without batches.").format(
                        item.name
                    ),
                    exc=VumaBulkError,
                )

            item.has_batch_no = 1
            item.has_expiry_date = 1 if track_expiry else 0
            item.save()
        elif track_expiry and not item.get("has_expiry_date"):
            item.has_expiry_date = 1
            item.save()
        elif not track_expiry and item.get("has_expiry_date"):
            frappe.throw(
                _("{} is expiry-tracked: an expiry date is required.").format(
                    item.name
                ),
                exc=VumaBulkError,
            )

        return item.name, False

    if not item_name:
        frappe.throw(
            _("New product needs a name (row for '{}').").format(code),
            exc=VumaBulkError,
        )

    comp = frappe.get_doc("Company", company)
    item_code = code or item_name.strip().upper().replace(" ", "-")[:40]

    if frappe.db.exists("Item", item_code):
        return item_code, False

    item = frappe.new_doc("Item")
    item.item_code = item_code
    item.item_name = item_name.strip()
    item.item_group = _leaf_group("Item Group", "All Item Groups")
    item.stock_uom = "Nos"
    item.is_stock_item = 1
    item.has_batch_no = 1
    item.has_expiry_date = 1 if track_expiry else 0
    item.append(
        "item_defaults",
        {
            "company": company,
            "default_warehouse": warehouse,
            "income_account": comp.get("default_income_account"),
            "expense_account": comp.get("default_expense_account"),
        },
    )
    item.insert()

    if code and code != item_code:
        item.append("barcodes", {"barcode": code})
        item.save()

    return item.name, True


def _ensure_bulk_batch(
    item_code, expiry_date=None, manufacturing_date=None, no_expiry=False
):
    """Get or create the batch for an item + expiry date (one lot).

    no_expiry=True reuses a single dateless batch per item.
    """
    if no_expiry:
        batch_id = f"{item_code}/NOEXPIRY"

        if frappe.db.exists("Batch", batch_id):
            return batch_id, False

        batch = frappe.new_doc("Batch")
        batch.batch_id = batch_id
        batch.item = item_code
        batch.manufacturing_date = (
            manufacturing_date or datetime.date.today()
        )
        batch.insert()

        return batch_id, True

    base = f"{item_code}/{expiry_date.strftime('%Y%m%d')}"
    batch_id = base
    suffix = 2

    while frappe.db.exists("Batch", batch_id):
        existing = frappe.get_doc("Batch", batch_id)

        if existing.item != item_code:
            batch_id = f"{base}-{suffix}"
            suffix += 1
            continue

        existing_expiry = existing.get("expiry_date")

        if existing_expiry and str(existing_expiry) != str(expiry_date):
            frappe.throw(
                _("Batch {} already exists with a different expiry.").format(
                    batch_id
                ),
                exc=VumaBulkError,
            )

        return batch_id, False

    batch = frappe.new_doc("Batch")
    batch.batch_id = batch_id
    batch.item = item_code
    batch.manufacturing_date = manufacturing_date or datetime.date.today()
    batch.expiry_date = expiry_date
    batch.insert()

    return batch_id, True


def _require_purchasing():
    assert_module_enabled("PUR")


@frappe.whitelist()
def dashboard():
    _require_purchasing()

    company = frappe.defaults.get_user_default(
        "Company"
    )

    supplier_count = frappe.db.count(
        "Supplier"
    )

    purchase_order_count = frappe.db.count(
        "Purchase Order",
        filters={
            "docstatus": 1,
        },
    )

    purchase_receipt_count = frappe.db.count(
        "Purchase Receipt",
        filters={
            "docstatus": 1,
        },
    )

    purchase_invoice_count = frappe.db.count(
        "Purchase Invoice",
        filters={
            "docstatus": 1,
        },
    )

    return success(
        data={
            "company": company,
            "suppliers": supplier_count,
            "purchase_orders": purchase_order_count,
            "purchase_receipts": purchase_receipt_count,
            "purchase_invoices": purchase_invoice_count,
        }
    )


@frappe.whitelist()
def suppliers(
    search=None,
    limit=50,
    start=0,
):
    _require_purchasing()

    limit = min(
        max(int(limit), 1),
        200,
    )

    start = max(
        int(start),
        0,
    )

    filters = {}

    or_filters = None

    if search:
        search = search.strip()

        or_filters = {
            "name": [
                "like",
                f"%{search}%",
            ],
            "supplier_name": [
                "like",
                f"%{search}%",
            ],
        }

    rows = frappe.get_all(
        "Supplier",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "supplier_name",
            "supplier_group",
            "territory",
            "supplier_type",
            "disabled",
            "creation",
            "modified",
        ],
        order_by="modified desc",
        start=start,
        page_length=limit,
    )

    total = frappe.db.count(
        "Supplier"
    )

    return success(
        data={
            "items": rows,
            "total": total,
            "start": start,
            "limit": limit,
        }
    )


@frappe.whitelist()
def purchase_orders(
    limit=50,
    start=0,
):
    _require_purchasing()

    rows = frappe.get_all(
        "Purchase Order",
        fields=[
            "name",
            "supplier",
            "supplier_name",
            "transaction_date",
            "schedule_date",
            "grand_total",
            "currency",
            "status",
            "per_received",
            "per_billed",
            "docstatus",
            "modified",
        ],
        order_by="modified desc",
        start=max(int(start), 0),
        page_length=min(
            max(int(limit), 1),
            200,
        ),
    )

    return success(
        data={
            "items": rows,
        }
    )


@frappe.whitelist()
def purchase_receipts(
    limit=50,
    start=0,
):
    _require_purchasing()

    rows = frappe.get_all(
        "Purchase Receipt",
        fields=[
            "name",
            "supplier",
            "supplier_name",
            "posting_date",
            "grand_total",
            "currency",
            "status",
            "per_billed",
            "docstatus",
            "modified",
        ],
        order_by="modified desc",
        start=max(int(start), 0),
        page_length=min(
            max(int(limit), 1),
            200,
        ),
    )

    return success(
        data={
            "items": rows,
        }
    )


@frappe.whitelist()
def purchase_invoices(
    limit=50,
    start=0,
):
    _require_purchasing()

    rows = frappe.get_all(
        "Purchase Invoice",
        fields=[
            "name",
            "supplier",
            "supplier_name",
            "posting_date",
            "due_date",
            "grand_total",
            "outstanding_amount",
            "currency",
            "status",
            "docstatus",
            "modified",
        ],
        order_by="modified desc",
        start=max(int(start), 0),
        page_length=min(
            max(int(limit), 1),
            200,
        ),
    )

    return success(
        data={
            "items": rows,
        }
    )


@frappe.whitelist()
def create_purchase_order(data=None):
    _require_purchasing()
    data = frappe.parse_json(data or {})

    doc = frappe.new_doc("Purchase Order", data)
    doc.insert()

    return success(
        data={
            "name": doc.name,
            "doctype": "Purchase Order",
            "docstatus": doc.docstatus,
        }
    )


@frappe.whitelist()
def create_purchase_invoice(data=None):
    _require_purchasing()
    data = frappe.parse_json(data or {})

    doc = frappe.new_doc("Purchase Invoice", data)
    doc.insert()

    return success(
        data={
            "name": doc.name,
            "doctype": "Purchase Invoice",
            "docstatus": doc.docstatus,
        }
    )


@frappe.whitelist()
def submit_purchase_order(name: str):
    _require_purchasing()

    doc = frappe.get_doc("Purchase Order", name)
    doc.submit()

    return success(
        data={
            "name": doc.name,
            "docstatus": doc.docstatus,
        }
    )


@frappe.whitelist()
def submit_purchase_invoice(name: str):
    _require_purchasing()

    doc = frappe.get_doc("Purchase Invoice", name)
    doc.submit()

    return success(
        data={
            "name": doc.name,
            "docstatus": doc.docstatus,
        }
    )


@frappe.whitelist()
def get_purchase_order(name: str):
    _require_purchasing()

    doc = frappe.get_doc("Purchase Order", name)

    return success(
        data=doc.as_dict()
    )


@frappe.whitelist()
def get_purchase_invoice(name: str):
    _require_purchasing()

    doc = frappe.get_doc("Purchase Invoice", name)

    return success(
        data=doc.as_dict()
    )


@frappe.whitelist()
def update_purchase_order(name: str, data=None):
    _require_purchasing()
    data = frappe.parse_json(data or {})

    doc = frappe.get_doc("Purchase Order", name)
    doc.update(data)
    doc.save()

    return success(
        data={
            "name": doc.name,
            "docstatus": doc.docstatus,
        }
    )


@frappe.whitelist()
def update_purchase_invoice(name: str, data=None):
    _require_purchasing()
    data = frappe.parse_json(data or {})

    doc = frappe.get_doc("Purchase Invoice", name)
    doc.update(data)
    doc.save()

    return success(
        data={
            "name": doc.name,
            "docstatus": doc.docstatus,
        }
    )


@frappe.whitelist()
def bulk_lookup(code: str):
    _require_purchasing()

    name = _resolve_bulk_item(code)

    if not name:
        return success(data={"found": False})

    item = frappe.get_doc("Item", name)

    return success(
        data={
            "found": True,
            "item_code": item.name,
            "item_name": item.get("item_name"),
            "uom": item.get("stock_uom"),
            "has_batch": bool(item.get("has_batch_no")),
        }
    )


@frappe.whitelist()
def bulk_receive(
    company: str,
    supplier: str,
    warehouse: str,
    posting_date: str = None,
    lines=None,
):
    """Receive a wholesale run: many products, each with its own expiry.

    lines: [{code, item_name, qty, rate, expiry_date, manufacturing_date?}]
    Creates missing items (batch-tracked) and exact-dated batches,
    then posts one submitted Purchase Receipt. All-or-nothing.
    """
    _require_purchasing()

    lines = frappe.parse_json(lines or [])

    company = str(company or "").strip()

    if not frappe.db.exists("Company", company):
        frappe.throw(
            _("Company {} not found.").format(company),
            exc=VumaBulkError,
        )

    supplier = str(supplier or "").strip()

    if not supplier:
        frappe.throw(
            _("Supplier is required."),
            exc=VumaBulkError,
        )

    if not frappe.db.exists("Supplier", supplier):
        created_supplier = frappe.new_doc("Supplier")
        created_supplier.supplier_name = supplier
        created_supplier.supplier_group = _leaf_group(
            "Supplier Group", "All Supplier Groups"
        )
        created_supplier.insert()
        supplier = created_supplier.name

    warehouse = str(warehouse or "").strip()
    warehouse_company = frappe.db.get_value(
        "Warehouse", warehouse, "company"
    )

    if not warehouse_company:
        frappe.throw(
            _("Warehouse {} not found.").format(warehouse),
            exc=VumaBulkError,
        )

    if warehouse_company != company:
        frappe.throw(
            _("Warehouse {} belongs to {}.").format(
                warehouse, warehouse_company
            ),
            exc=VumaBulkError,
        )

    if posting_date:
        posting_date = frappe.utils.getdate(posting_date)
    else:
        posting_date = datetime.date.today()

    if not lines:
        frappe.throw(
            _("Add at least one line."),
            exc=VumaBulkError,
        )

    if len(lines) > 2000:
        frappe.throw(
            _("Too many lines (max 2000)."),
            exc=VumaBulkError,
        )

    prepared = []
    items_created = []
    batches_created = []

    for pos, line in enumerate(lines, start=1):
        line = line or {}
        code = str(line.get("code") or "").strip()
        item_name = str(line.get("item_name") or "").strip()

        try:
            qty = float(line.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0

        try:
            rate = float(line.get("rate") or 0)
        except (TypeError, ValueError):
            rate = 0

        if not code and not item_name:
            frappe.throw(
                _("Line {}: enter a barcode, code or name.").format(pos),
                exc=VumaBulkError,
            )

        if qty <= 0:
            frappe.throw(
                _("Line {}: quantity must be above zero.").format(pos),
                exc=VumaBulkError,
            )

        if rate < 0:
            frappe.throw(
                _("Line {}: rate cannot be negative.").format(pos),
                exc=VumaBulkError,
            )

        expiry_raw = str(line.get("expiry_date") or "").strip()
        no_expiry = bool(line.get("no_expiry")) or expiry_raw.lower() in (
            "none",
            "no-expiry",
            "noexpiry",
            "-",
        )

        expiry_date = None

        if not no_expiry:
            if not expiry_raw:
                frappe.throw(
                    _("Line {}: expiry date is required.").format(pos),
                    exc=VumaBulkError,
                )

            try:
                expiry_date = frappe.utils.getdate(expiry_raw)
            except Exception:
                frappe.throw(
                    _(
                        "Line {}: expiry date '{}' is not a valid date."
                    ).format(pos, expiry_raw),
                    exc=VumaBulkError,
                )

            if expiry_date <= posting_date:
                frappe.throw(
                    _(
                        "Line {}: expiry must be after the receipt date."
                    ).format(pos),
                    exc=VumaBulkError,
                )

        manufacturing_raw = str(
            line.get("manufacturing_date") or ""
        ).strip()
        manufacturing_date = None

        if manufacturing_raw:
            try:
                manufacturing_date = frappe.utils.getdate(
                    manufacturing_raw
                )
            except Exception:
                frappe.throw(
                    _(
                        "Line {}: manufacturing date '{}' is not valid."
                    ).format(pos, manufacturing_raw),
                    exc=VumaBulkError,
                )

        item_code, created_item = _ensure_bulk_item(
            code,
            item_name,
            company,
            warehouse,
            track_expiry=not no_expiry,
        )

        if created_item:
            items_created.append(item_code)

        batch_id, created_batch = _ensure_bulk_batch(
            item_code,
            expiry_date,
            manufacturing_date,
            no_expiry=no_expiry,
        )

        if created_batch:
            batches_created.append(batch_id)

        prepared.append(
            {
                "item_code": item_code,
                "qty": qty,
                "rate": rate,
                "warehouse": warehouse,
                "batch_no": batch_id,
            }
        )

    receipt = frappe.new_doc("Purchase Receipt")
    receipt.supplier = supplier
    receipt.company = company
    receipt.posting_date = posting_date
    receipt.set_posting_time = 1

    for entry in prepared:
        receipt.append("items", entry)

    receipt.insert()
    receipt.submit()

    return success(
        data={
            "receipt": receipt.name,
            "lines": len(prepared),
            "units": round(
                sum(entry["qty"] for entry in prepared), 2
            ),
            "total": round(
                sum(
                    entry["qty"] * entry["rate"]
                    for entry in prepared
                ),
                2,
            ),
            "items_created": items_created,
            "batches_created": batches_created,
        }
    )