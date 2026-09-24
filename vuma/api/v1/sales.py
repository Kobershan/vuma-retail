import frappe
from frappe.utils import now_datetime

from vuma.api.v1.responses import success
from vuma.licensing.entitlements import assert_module_enabled


class VumaPickingError(frappe.ValidationError):
    pass


OPEN_SO_STATUSES = [
    "To Deliver and Bill",
    "To Deliver",
    "To Bill",
    "Draft",
]


def _require_sales():
    assert_module_enabled("SAL")


@frappe.whitelist()
def dashboard():
    _require_sales()

    company = frappe.defaults.get_user_default(
        "Company"
    )

    customer_count = frappe.db.count(
        "Customer"
    )

    quotation_count = frappe.db.count(
        "Quotation",
        filters={
            "docstatus": ["<", 2],
        },
    )

    sales_order_count = frappe.db.count(
        "Sales Order",
        filters={
            "docstatus": 1,
        },
    )

    delivery_note_count = frappe.db.count(
        "Delivery Note",
        filters={
            "docstatus": 1,
        },
    )

    sales_invoice_count = frappe.db.count(
        "Sales Invoice",
        filters={
            "docstatus": 1,
        },
    )

    return success(
        data={
            "company": company,
            "customers": customer_count,
            "quotations": quotation_count,
            "sales_orders": sales_order_count,
            "delivery_notes": delivery_note_count,
            "sales_invoices": sales_invoice_count,
        }
    )


@frappe.whitelist()
def customers(
    search=None,
    limit=50,
    start=0,
):
    _require_sales()

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
            "customer_name": [
                "like",
                f"%{search}%",
            ],
        }

    rows = frappe.get_all(
        "Customer",
        filters=filters,
        or_filters=or_filters,
        fields=[
            "name",
            "customer_name",
            "customer_group",
            "territory",
            "customer_type",
            "disabled",
            "creation",
            "modified",
        ],
        order_by="modified desc",
        start=start,
        page_length=limit,
    )

    total = frappe.db.count(
        "Customer"
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
def quotations(
    limit=50,
    start=0,
):
    _require_sales()

    rows = frappe.get_all(
        "Quotation",
        fields=[
            "name",
            "quotation_to",
            "party_name",
            "transaction_date",
            "valid_till",
            "grand_total",
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
def orders(
    limit=50,
    start=0,
):
    _require_sales()

    rows = frappe.get_all(
        "Sales Order",
        fields=[
            "name",
            "customer",
            "customer_name",
            "transaction_date",
            "delivery_date",
            "grand_total",
            "currency",
            "status",
            "per_delivered",
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
def delivery_notes(
    limit=50,
    start=0,
):
    _require_sales()

    rows = frappe.get_all(
        "Delivery Note",
        fields=[
            "name",
            "customer",
            "customer_name",
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
def invoices(
    limit=50,
    start=0,
):
    _require_sales()

    rows = frappe.get_all(
        "Sales Invoice",
        fields=[
            "name",
            "customer",
            "customer_name",
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
def create_sales_order(data=None):
    _require_sales()
    data = frappe.parse_json(data or {})
    doc = frappe.new_doc("Sales Order", data)
    doc.insert()
    return success(data={"name": doc.name, "doctype": "Sales Order", "docstatus": doc.docstatus})


@frappe.whitelist()
def create_quotation(data=None):
    _require_sales()
    data = frappe.parse_json(data or {})
    doc = frappe.new_doc("Quotation", data)
    doc.insert()
    return success(data={"name": doc.name, "doctype": "Quotation", "docstatus": doc.docstatus})


@frappe.whitelist()
def create_delivery_note(data=None):
    _require_sales()
    data = frappe.parse_json(data or {})
    doc = frappe.new_doc("Delivery Note", data)
    doc.insert()
    return success(data={"name": doc.name, "doctype": "Delivery Note", "docstatus": doc.docstatus})


@frappe.whitelist()
def create_sales_invoice(data=None):
    _require_sales()
    data = frappe.parse_json(data or {})
    doc = frappe.new_doc("Sales Invoice", data)
    doc.insert()
    return success(data={"name": doc.name, "doctype": "Sales Invoice", "docstatus": doc.docstatus})


@frappe.whitelist()
def submit_sales_order(name: str):
    _require_sales()
    doc = frappe.get_doc("Sales Order", name)
    doc.submit()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def submit_quotation(name: str):
    _require_sales()
    doc = frappe.get_doc("Quotation", name)
    doc.submit()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def submit_delivery_note(name: str):
    _require_sales()
    doc = frappe.get_doc("Delivery Note", name)
    doc.submit()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def submit_sales_invoice(name: str):
    _require_sales()
    doc = frappe.get_doc("Sales Invoice", name)
    doc.submit()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def get_sales_order(name: str):
    _require_sales()
    doc = frappe.get_doc("Sales Order", name)
    return success(data=doc.as_dict())


@frappe.whitelist()
def get_quotation(name: str):
    _require_sales()
    doc = frappe.get_doc("Quotation", name)
    return success(data=doc.as_dict())


@frappe.whitelist()
def get_delivery_note(name: str):
    _require_sales()
    doc = frappe.get_doc("Delivery Note", name)
    return success(data=doc.as_dict())


@frappe.whitelist()
def get_sales_invoice(name: str):
    _require_sales()
    doc = frappe.get_doc("Sales Invoice", name)
    return success(data=doc.as_dict())


@frappe.whitelist()
def update_sales_order(name: str, data=None):
    _require_sales()
    doc = frappe.get_doc("Sales Order", name)
    data = frappe.parse_json(data or {})
    doc = frappe.get_doc("Sales Order", name)
    doc.update(data)
    doc.save()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def update_quotation(name: str, data=None):
    _require_sales()
    doc = frappe.get_doc("Quotation", name)
    data = frappe.parse_json(data or {})
    doc = frappe.get_doc("Quotation", name)
    doc.update(data)
    doc.save()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


@frappe.whitelist()
def update_delivery_note(name: str, data=None):
    _require_sales()
    doc = frappe.get_doc("Delivery Note", name)
    data = frappe.parse_json(data or {})
    doc = frappe.get_doc("Delivery Note", name)
    doc.update(data)
    doc.save()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})


def _customer_city(customer, cache):
    if customer in cache:
        return cache[customer]

    rows = frappe.db.sql(
        """select a.city from tabAddress a
        join `tabDynamic Link` l on l.parent = a.name
        where l.link_doctype = 'Customer' and l.link_name = %s
        and a.city is not null and a.city != ''
        order by a.is_shipping_address desc,
                 a.is_primary_address desc limit 1""",
        (customer,),
    )

    city = (rows[0][0] if rows else "") or ""
    cache[customer] = city

    return city


def _open_pick_orders(company=None):
    filters = {
        "docstatus": 1,
        "status": ["not in", ["Completed", "Closed", "Cancelled"]],
    }

    if company:
        if not frappe.db.exists("Company", company):
            frappe.throw(
                "Company {} not found.".format(company),
                exc=VumaPickingError,
            )

        filters["company"] = company

    return frappe.get_all(
        "Sales Order",
        filters=filters,
        fields=[
            "name",
            "customer",
            "customer_name",
            "company",
            "transaction_date",
            "status",
        ],
        order_by="transaction_date asc",
        limit_page_length=500,
    )


PICKING_GROUPS = ("Order", "Suburb", "City")


def _active_pick_orders():
    rows = frappe.db.sql(
        """select distinct i.sales_order
        from `tabVuma Pick Slip Item` i
        join `tabVuma Pick Slip` s on s.name = i.parent
        where s.status in ('Available', 'In Progress')
        and i.sales_order is not null and i.sales_order != ''""",
        as_dict=True,
    )
    return {row.sales_order for row in rows}


def _pickable_orders(company=None):
    """Open, undelivered orders that are not assigned to an active slip."""
    assigned = _active_pick_orders()
    cities: dict[str, str] = {}
    orders = []

    for order in _open_pick_orders(company):
        if order.name in assigned:
            continue

        items = frappe.db.sql(
            """select name, item_code, item_name, qty, delivered_qty,
            uom, warehouse from `tabSales Order Item`
            where parent = %s order by idx asc""",
            (order.name,),
            as_dict=True,
        )
        lines = [
            item for item in items
            if float(item.qty or 0) - float(item.delivered_qty or 0) > 0
        ]

        if not lines:
            continue

        orders.append(
            {
                "name": order.name,
                "customer": order.customer,
                "customer_name": order.customer_name,
                "company": order.company,
                "city": _customer_city(order.customer, cities) or "Unspecified",
                "transaction_date": str(order.transaction_date or ""),
                "status": order.status,
                "units": round(sum(
                    float(item.qty or 0) - float(item.delivered_qty or 0)
                    for item in lines
                ), 2),
                "items": lines,
            }
        )

    return orders


def _slip_data(slip):
    lines = [
        {
            "name": row.name,
            "item_code": row.item_code,
            "item_name": row.item_name or row.item_code,
            "qty": float(row.qty or 0),
            "uom": row.uom or "Nos",
            "warehouse": row.warehouse,
            "company": row.company,
            "sales_order": row.sales_order,
            "customer": row.customer,
            "customer_name": row.customer_name,
            "city": row.city,
            "checked": bool(row.checked),
            "checked_by": row.checked_by,
            "checked_at": str(row.checked_at or ""),
        }
        for row in slip.get("items") or []
    ]
    lines.sort(key=lambda row: (
        row["company"] or "", row["city"] or "", row["sales_order"] or "",
        row["item_code"] or "",
    ))

    return {
        "name": slip.name,
        "status": slip.status,
        "grouping": slip.grouping,
        "area": slip.area,
        "company": slip.company,
        "started_by": slip.started_by,
        "started_at": str(slip.started_at or ""),
        "completed_by": slip.completed_by,
        "completed_at": str(slip.completed_at or ""),
        "orders": sorted({row["sales_order"] for row in lines}),
        "lines": lines,
        "units": round(sum(row["qty"] for row in lines), 2),
        "checked_lines": sum(1 for row in lines if row["checked"]),
    }


@frappe.whitelist()
def picking_board(company: str = None, grouping: str = "Suburb"):
    """Shared queue plus saved slips for the Vuma picking workboard."""
    _require_sales()
    grouping = str(grouping or "Suburb").title()

    if grouping not in PICKING_GROUPS:
        frappe.throw("Choose Order, Suburb, or City.", exc=VumaPickingError)

    groups: dict[str, dict] = {}

    for order in _pickable_orders(company):
        key = order["name"] if grouping == "Order" else order["city"]
        entry = groups.setdefault(
            key,
            {
                "key": key,
                "label": key,
                "grouping": grouping,
                "orders": [],
                "companies": set(),
                "units": 0.0,
                "lines": 0,
                "preview": [],
            },
        )
        entry["orders"].append(order["name"])
        entry["companies"].add(order["company"])
        entry["units"] += order["units"]
        entry["lines"] += len(order["items"])
        entry["preview"].extend([
            {
                "item_code": item.item_code,
                "item_name": item.item_name or item.item_code,
                "qty": float(item.qty or 0) - float(item.delivered_qty or 0),
                "uom": item.uom or "Nos",
                "warehouse": item.warehouse,
                "company": order["company"],
                "sales_order": order["name"],
                "customer_name": order["customer_name"],
                "city": order["city"],
            }
            for item in order["items"]
        ])

    available = [
        {
            **entry,
            "companies": sorted(entry["companies"]),
            "units": round(entry["units"], 2),
            "preview": sorted(entry["preview"], key=lambda line: (
                line["company"], line["city"], line["sales_order"],
                line["item_code"],
            )),
        }
        for entry in groups.values()
    ]
    available.sort(key=lambda entry: (-entry["units"], entry["label"]))

    slips = []
    filters = {}
    if company:
        # Multi-company slips have an empty company field, so retain them.
        filters["company"] = ["in", [company, ""]]

    for row in frappe.get_all(
        "Vuma Pick Slip",
        filters=filters,
        fields=["name"],
        order_by="modified desc",
        limit_page_length=100,
    ):
        if frappe.has_permission("Vuma Pick Slip", "read", doc=row.name):
            slips.append(_slip_data(frappe.get_doc("Vuma Pick Slip", row.name)))

    return success(data={"grouping": grouping, "available": available, "slips": slips})


@frappe.whitelist()
def start_picking_slip(grouping: str, orders=None):
    """Start one shared slip from an available order or area group."""
    _require_sales()
    grouping = str(grouping or "").title()
    orders = [str(name).strip() for name in frappe.parse_json(orders or []) if str(name).strip()]
    orders = list(dict.fromkeys(orders))

    if grouping not in PICKING_GROUPS or not orders:
        frappe.throw("A grouping and at least one order are required.", exc=VumaPickingError)

    pickable = {order["name"]: order for order in _pickable_orders()}
    missing = [name for name in orders if name not in pickable]
    if missing:
        frappe.throw(
            "These orders are no longer available: {}.".format(", ".join(missing)),
            exc=VumaPickingError,
        )

    selected = [pickable[name] for name in orders]
    areas = {order["city"] for order in selected}

    if grouping == "Order" and len(selected) != 1:
        frappe.throw("An order slip can contain one order only.", exc=VumaPickingError)
    if grouping in ("Suburb", "City") and len(areas) != 1:
        frappe.throw("An area slip must contain orders from one area.", exc=VumaPickingError)

    companies = {order["company"] for order in selected}
    slip = frappe.new_doc("Vuma Pick Slip")
    slip.status = "In Progress"
    slip.grouping = grouping
    slip.area = selected[0]["name"] if grouping == "Order" else selected[0]["city"]
    slip.company = next(iter(companies)) if len(companies) == 1 else ""
    slip.started_by = frappe.session.user
    slip.started_at = now_datetime()

    for order in selected:
        for item in order["items"]:
            qty = float(item.qty or 0) - float(item.delivered_qty or 0)
            slip.append("items", {
                "item_code": item.item_code,
                "item_name": item.item_name or item.item_code,
                "qty": qty,
                "uom": item.uom or "Nos",
                "warehouse": item.warehouse,
                "company": order["company"],
                "sales_order": order["name"],
                "customer": order["customer"],
                "customer_name": order["customer_name"],
                "city": order["city"],
            })

    slip.insert()
    data = _slip_data(slip)
    frappe.publish_realtime("vuma_pick_slip_update", {"slip": data}, after_commit=True)
    return success(data=data)


@frappe.whitelist()
def set_picking_line_checked(slip_name: str, line: str, checked=0):
    """Check a shared slip line and advance/complete the slip as needed."""
    _require_sales()
    slip_name = str(slip_name or "").strip()
    line = str(line or "").strip()
    slip = frappe.get_doc("Vuma Pick Slip", slip_name)

    if not frappe.has_permission("Vuma Pick Slip", "write", doc=slip):
        frappe.throw("You cannot update this picking slip.", exc=frappe.PermissionError)

    row = frappe.db.get_value(
        "Vuma Pick Slip Item", line, ["parent", "parenttype"], as_dict=True
    )
    if not row or row.parenttype != "Vuma Pick Slip" or row.parent != slip.name:
        frappe.throw("Picking slip line not found.", exc=VumaPickingError)

    checked = str(checked).lower() in ("1", "true", "yes")
    frappe.db.set_value("Vuma Pick Slip Item", line, {
        "checked": int(checked),
        "checked_by": frappe.session.user if checked else None,
        "checked_at": now_datetime() if checked else None,
    }, update_modified=True)

    total = frappe.db.count("Vuma Pick Slip Item", {"parent": slip.name})
    done = frappe.db.count("Vuma Pick Slip Item", {"parent": slip.name, "checked": 1})
    values = {"status": "Completed" if total and total == done else "In Progress"}
    if values["status"] == "Completed":
        values.update({"completed_by": frappe.session.user, "completed_at": now_datetime()})
    else:
        values.update({"completed_by": None, "completed_at": None})
    frappe.db.set_value("Vuma Pick Slip", slip.name, values, update_modified=True)

    data = _slip_data(frappe.get_doc("Vuma Pick Slip", slip.name))
    frappe.publish_realtime("vuma_pick_slip_update", {"slip": data}, after_commit=True)
    return success(data=data)


@frappe.whitelist()
def picking_queue(company: str = None):
    """Open sales orders grouped by town/suburb for bulk picking."""
    _require_sales()

    orders = []
    areas: dict[str, dict] = {}
    cities: dict[str, str] = {}

    for order in _open_pick_orders(company):
        lines = frappe.db.sql(
            """select sum(qty - delivered_qty) as units,
            count(*) as line_count from `tabSales Order Item`
            where parent = %s and (qty - delivered_qty) > 0""",
            (order.name,),
            as_dict=True,
        )

        units = float((lines[0].get("units") if lines else 0) or 0)

        if units <= 0:
            continue

        city = _customer_city(order.customer, cities) or "Unspecified"

        entry = {
            "sales_order": order.name,
            "customer": order.customer,
            "customer_name": order.get("customer_name"),
            "company": order.company,
            "city": city,
            "transaction_date": str(order.get("transaction_date") or ""),
            "status": order.status,
            "units": units,
        }
        orders.append(entry)

        area = areas.setdefault(
            city, {"city": city, "orders": 0, "units": 0.0}
        )
        area["orders"] += 1
        area["units"] += units

    return success(
        data={
            "orders": orders,
            "areas": sorted(
                areas.values(),
                key=lambda area: area["units"],
                reverse=True,
            ),
            "companies": [
                {
                    "name": company.name,
                    "warehouses": [
                        row.name
                        for row in frappe.get_all(
                            "Warehouse",
                            filters={"company": company.name},
                            order_by="name asc",
                            limit_page_length=100,
                        )
                    ],
                }
                for company in frappe.get_all(
                    "Company", order_by="name asc", limit_page_length=50
                )
            ],
        }
    )


def _pick_slip_data(pick):
    """Return the tablet/print representation of one Delivery Pick List."""
    lines = []
    order_names = {
        row.sales_order
        for row in pick.get("locations") or []
        if row.sales_order
    }
    customers = {
        row.name: row
        for row in frappe.get_all(
            "Sales Order",
            filters={"name": ["in", list(order_names)]},
            fields=["name", "customer", "customer_name"],
        )
    } if order_names else {}

    for row in pick.get("locations") or []:
        customer = customers.get(row.sales_order)

        lines.append(
            {
                "name": row.name,
                "item_code": row.item_code,
                "item_name": row.item_name or row.item_code,
                "qty": float(row.qty or 0),
                "uom": row.uom or row.stock_uom or "Nos",
                "warehouse": row.warehouse,
                "batch_no": row.batch_no,
                "sales_order": row.sales_order,
                "customer": customer.customer if customer else None,
                "customer_name": (
                    customer.customer_name if customer else None
                ),
                "checked": bool(row.get("custom_vuma_picked_check")),
            }
        )

    return {
        "name": pick.name,
        "company": pick.company,
        "warehouse": pick.parent_warehouse,
        "status": pick.status,
        "delivery_status": pick.delivery_status,
        "creation": str(pick.creation or ""),
        "orders": sorted({
            line["sales_order"] for line in lines if line["sales_order"]
        }),
        "lines": lines,
        "units": round(sum(line["qty"] for line in lines), 2),
        "checked_lines": sum(1 for line in lines if line["checked"]),
    }


@frappe.whitelist()
def pick_slips(company: str = None, name: str = None):
    """Recent Delivery Pick Lists, including the print/tablet slip lines."""
    _require_sales()

    filters = {
        "purpose": "Delivery",
        "docstatus": 1,
    }

    if company:
        filters["company"] = company

    if name:
        filters["name"] = name

    slips = []

    for entry in frappe.get_all(
        "Pick List",
        filters=filters,
        fields=["name"],
        order_by="modified desc",
        limit_page_length=50,
    ):
        if not frappe.has_permission(
            "Pick List", "read", doc=entry.name
        ):
            continue

        slips.append(
            _pick_slip_data(
                frappe.get_doc("Pick List", entry.name)
            )
        )

    return success(data={"slips": slips})


@frappe.whitelist()
def set_pick_slip_line_checked(
    pick_list: str,
    line: str,
    checked=0,
):
    """Persist a picker confirmation without changing stock or delivery data."""
    _require_sales()

    pick_list = str(pick_list or "").strip()
    line = str(line or "").strip()

    if not pick_list or not line:
        frappe.throw(
            "Pick list and line are required.",
            exc=VumaPickingError,
        )

    if not frappe.db.exists(
        "Pick List",
        {
            "name": pick_list,
            "purpose": "Delivery",
            "docstatus": 1,
        },
    ):
        frappe.throw(
            "Delivery Pick List {} not found.".format(pick_list),
            exc=VumaPickingError,
        )

    if not frappe.has_permission(
        "Pick List", "write", doc=pick_list
    ):
        frappe.throw(
            "You do not have access to Pick List {}.".format(pick_list),
            exc=frappe.PermissionError,
        )

    row = frappe.db.get_value(
        "Pick List Item",
        line,
        ["parent", "parenttype"],
        as_dict=True,
    )

    if not row or row.parenttype != "Pick List" or row.parent != pick_list:
        frappe.throw(
            "Pick List line {} was not found.".format(line),
            exc=VumaPickingError,
        )

    frappe.db.set_value(
        "Pick List Item",
        line,
        "custom_vuma_picked_check",
        1 if str(checked).lower() in ("1", "true", "yes") else 0,
        update_modified=True,
    )

    return success(
        data=_pick_slip_data(
            frappe.get_doc("Pick List", pick_list)
        )
    )


@frappe.whitelist()
def create_pick_list(
    company: str,
    warehouse: str,
    orders=None,
    city: str = None,
):
    """Create a submitted Pick List (purpose=Delivery).

    Pass explicit `orders`, or a `city` to bulk-pull every open order
    in that suburb/town. Multi-order picks group the same items so the
    floor pulls in bulk, while each line keeps its sales order ref so
    packing separates per order afterwards.
    """
    _require_sales()

    company = str(company or "").strip()

    if not frappe.db.exists("Company", company):
        frappe.throw(
            "Company {} not found.".format(company),
            exc=VumaPickingError,
        )

    warehouse = str(warehouse or "").strip()
    warehouse_company = frappe.db.get_value(
        "Warehouse", warehouse, "company"
    )

    if not warehouse_company:
        frappe.throw(
            "Warehouse {} not found.".format(warehouse),
            exc=VumaPickingError,
        )

    if warehouse_company != company:
        frappe.throw(
            "Warehouse {} belongs to {}.".format(
                warehouse, warehouse_company
            ),
            exc=VumaPickingError,
        )

    orders = frappe.parse_json(orders or [])
    orders = [str(name).strip() for name in orders if str(name).strip()]
    cities: dict[str, str] = {}

    if city and not orders:
        for order in _open_pick_orders(company):
            if _customer_city(order.customer, cities) == city:
                orders.append(order.name)

    if not orders:
        frappe.throw(
            "No open orders to pick.",
            exc=VumaPickingError,
        )

    return success(
        data=_make_pick_list(company, warehouse, orders)
    )


def _make_pick_list(company, warehouse, orders):
    """Shared core: validate + post one submitted Delivery Pick List.

    Only unpicked quantities go on the slip; fully picked orders are
    reported as skipped instead of double-picking.
    """
    seen: dict[str, bool] = {}
    unique_orders = []

    for name in orders:
        if name not in seen:
            seen[name] = True
            unique_orders.append(name)

    locations = []
    skipped = []

    for name in unique_orders:
        if not frappe.db.exists("Sales Order", name):
            frappe.throw(
                "Sales Order {} not found.".format(name),
                exc=VumaPickingError,
            )

        order = frappe.get_doc("Sales Order", name)

        if order.docstatus != 1:
            frappe.throw(
                "Sales Order {} is not submitted.".format(name),
                exc=VumaPickingError,
            )

        if order.company != company:
            frappe.throw(
                "Sales Order {} belongs to {}.".format(
                    name, order.company
                ),
                exc=VumaPickingError,
            )

        if order.status in ("Completed", "Closed", "Cancelled"):
            frappe.throw(
                "Sales Order {} is {}.".format(name, order.status),
                exc=VumaPickingError,
            )

        so_items = [
            item.get("name")
            for item in order.get("items") or []
            if item.get("name")
        ]

        picked: dict[str, float] = {}

        if so_items:
            placeholders = ", ".join(["%s"] * len(so_items))

            for row in frappe.db.sql(
                f"""select i.sales_order_item,
                sum(i.picked_qty) as picked
                from `tabPick List Item` i
                join `tabPick List` p on p.name = i.parent
                where p.docstatus = 1
                and i.sales_order_item in ({placeholders})
                group by i.sales_order_item""",
                tuple(so_items),
                as_dict=True,
            ):
                picked[row.get("sales_order_item")] = float(
                    row.get("picked") or 0
                )

        order_lines = []

        for item in order.get("items") or []:
            pending = float(item.get("qty") or 0) - float(
                item.get("delivered_qty") or 0
            )
            pickable = (
                pending - picked.get(item.get("name"), 0.0)
            )

            if pickable <= 0:
                continue

            uom = (
                item.get("uom")
                or frappe.db.get_value(
                    "Item", item.get("item_code"), "stock_uom"
                )
                or "Nos"
            )

            order_lines.append(
                {
                    "item_code": item.get("item_code"),
                    "qty": pickable,
                    "stock_qty": pickable,
                    "uom": uom,
                    "conversion_factor": 1,
                    "warehouse": item.get("warehouse") or warehouse,
                    "sales_order": name,
                    "sales_order_item": item.get("name"),
                    "customer": order.customer,
                    "customer_name": order.get("customer_name"),
                }
            )

        if not order_lines:
            skipped.append(name)
            continue

        locations.extend(order_lines)

    if not locations:
        frappe.throw(
            "Nothing left to pick — these orders are already picked.",
            exc=VumaPickingError,
        )

    pick = frappe.new_doc("Pick List")
    pick.company = company
    pick.purpose = "Delivery"
    pick.parent_warehouse = warehouse
    pick.group_same_items = 1 if len(unique_orders) > 1 else 0

    for location in locations:
        pick.append(
            "locations",
            {key: location[key] for key in location if key in (
                "item_code", "qty", "stock_qty", "uom",
                "conversion_factor", "warehouse",
                "sales_order", "sales_order_item",
            )},
        )

    pick.insert()
    pick.submit()

    return {
        "pick_list": pick.name,
        "company": company,
        "orders": unique_orders,
        "skipped": skipped,
        "lines": len(locations),
        "units": round(
            sum(location["qty"] for location in locations), 2
        ),
        "slip_lines": [
            {
                "company": company,
                "warehouse": location["warehouse"],
                "item_code": location["item_code"],
                "item_name": frappe.db.get_value(
                    "Item", location["item_code"], "item_name"
                )
                or location["item_code"],
                "qty": location["qty"],
                "sales_order": location["sales_order"],
                "customer": location["customer"],
                "customer_name": location["customer_name"],
            }
            for location in locations
        ],
    }


@frappe.whitelist()
def create_area_picks(city: str, warehouses=None):
    """One suburb, all companies, one combined pick run.

    Creates a submitted Pick List per company holding open orders in
    `city` (using that company's warehouse from `warehouses`), and
    returns every line flattened into a single run slip the floor can
    pull — and pack — from.
    """
    _require_sales()

    city = str(city or "").strip()

    if not city:
        frappe.throw(
            "Suburb/town is required.",
            exc=VumaPickingError,
        )

    warehouses = frappe.parse_json(warehouses or {})
    cities: dict[str, str] = {}
    by_company: dict[str, list] = {}

    for order in _open_pick_orders(None):
        if _customer_city(order.customer, cities) != city:
            continue

        by_company.setdefault(order.company, []).append(order.name)

    if not by_company:
        frappe.throw(
            "No open orders in {}.".format(city),
            exc=VumaPickingError,
        )

    picks = []
    combined = []
    skipped_all = []

    for company in sorted(by_company):
        warehouse = str((warehouses or {}).get(company) or "").strip()

        if not warehouse:
            frappe.throw(
                "Pick a warehouse for {}.".format(company),
                exc=VumaPickingError,
            )

        warehouse_company = frappe.db.get_value(
            "Warehouse", warehouse, "company"
        )

        if warehouse_company != company:
            frappe.throw(
                "Warehouse {} belongs to {}.".format(
                    warehouse, warehouse_company or "nobody"
                ),
                exc=VumaPickingError,
            )

        made = _make_pick_list(company, warehouse, by_company[company])
        picks.append(made)
        combined.extend(made["slip_lines"])
        skipped_all.extend(made["skipped"])

    combined.sort(
        key=lambda line: (
            line["company"],
            line["warehouse"],
            line["item_code"],
        )
    )

    return success(
        data={
            "city": city,
            "picks": picks,
            "combined": combined,
            "skipped": skipped_all,
            "lines": len(combined),
            "units": round(
                sum(line["qty"] for line in combined), 2
            ),
        }
    )


@frappe.whitelist()
def update_sales_invoice(name: str, data=None):
    _require_sales()
    doc = frappe.get_doc("Sales Invoice", name)
    data = frappe.parse_json(data or {})
    doc = frappe.get_doc("Sales Invoice", name)
    doc.update(data)
    doc.save()
    return success(data={"name": doc.name, "docstatus": doc.docstatus})
