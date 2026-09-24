"""Seed demo business data so the group overview dashboard lights up.

Run:
    bench --site vuma.localhost execute vuma.seed_dashboard.run

Idempotent: skips entirely if VUMA seed invoices already exist.
All created records carry remarks = "VUMA seed" (where supported).
"""

from __future__ import annotations

import datetime

import frappe

SEED_REMARK = "VUMA seed"

COMPANIES = [
    {"name": "Trade Rite", "abbr": "TR"},
    {"name": "Trade Rite (Demo)", "abbr": "TRD"},
    {"name": "Siyaya DC", "abbr": "SIY"},
]

TERRITORIES = ["Johannesburg", "Cape Town", "Durban"]

ITEMS = [
    {"suffix": "WIDGET-A", "name": "Seed Widget A", "cost": 50.0, "price": 95.0},
    {"suffix": "WIDGET-B", "name": "Seed Widget B", "cost": 120.0, "price": 210.0},
    {"suffix": "GADGET-C", "name": "Seed Gadget C", "cost": 300.0, "price": 480.0},
]


def inspect():
    """Print the defaults the seeder will rely on."""
    out = {}

    out["item_groups"] = [
        r.name
        for r in frappe.get_all(
            "Item Group", filters={"is_group": 0}, limit=10
        )
    ]
    out["uoms"] = [
        r.name for r in frappe.get_all("UOM", limit=6)
    ]
    out["territories"] = [
        r.name for r in frappe.get_all("Territory", limit=20)
    ]
    out["customer_groups"] = [
        r.name for r in frappe.get_all("Customer Group", limit=10)
    ]
    out["supplier_groups"] = [
        r.name for r in frappe.get_all("Supplier Group", limit=10)
    ]

    out["companies"] = []
    for company in frappe.get_all(
        "Company",
        fields=[
            "name",
            "abbr",
            "default_currency",
            "default_receivable_account",
            "default_payable_account",
            "default_income_account",
            "default_expense_account",
            "default_bank_account",
            "default_cash_account",
            "cost_center",
            "enable_perpetual_inventory",
        ],
    ):
        out["companies"].append(dict(company))

    out["seed_invoices"] = frappe.db.count(
        "Sales Invoice", {"remarks": SEED_REMARK}
    )

    print(out)


def _first_day(year, month):
    return datetime.date(year, month, 1)


def _month_offsets(today, count):
    months = []
    year, month = today.year, today.month

    for back in range(count - 1, -1, -1):
        y, m = year, month - back
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    return months


def _ensure_territories():
    for territory in TERRITORIES:
        if not frappe.db.exists("Territory", territory):
            doc = frappe.new_doc("Territory")
            doc.territory_name = territory
            doc.parent_territory = "All Territories"
            doc.insert()


def _leaf_group(doctype, fallback):
    rows = frappe.get_all(
        doctype, filters={"is_group": 0}, limit=5
    )
    if rows:
        return rows[0].name
    return fallback


def backfill_payments():
    """Create the oldest-invoice payment for any seeded company missing one."""
    today = datetime.date.today()
    fixed = []

    for company in COMPANIES:
        cname = company["name"]

        seed_names = [
            r.name
            for r in frappe.get_all(
                "Sales Invoice",
                filters={
                    "remarks": SEED_REMARK,
                    "company": cname,
                    "docstatus": 1,
                },
            )
        ]

        if seed_names:
            linked = frappe.db.sql(
                """select distinct t.reference_name
                from `tabPayment Entry Reference` t
                join `tabPayment Entry` p on p.name = t.parent
                where p.docstatus = 1
                and t.reference_doctype = 'Sales Invoice'
                and t.reference_name in %(names)s""",
                {"names": tuple(seed_names)},
            )

            if linked:
                continue

        comp = frappe.get_doc("Company", cname)
        paid_to = comp.get("default_bank_account") or comp.get(
            "default_cash_account"
        )
        is_bank = bool(comp.get("default_bank_account"))

        oldest = frappe.get_all(
            "Sales Invoice",
            filters={
                "remarks": SEED_REMARK,
                "company": cname,
                "docstatus": 1,
                "outstanding_amount": [">", 0],
            },
            fields=["name", "customer", "outstanding_amount"],
            order_by="posting_date asc",
            limit=1,
        )

        if not oldest:
            continue

        inv = oldest[0]
        payment = frappe.new_doc("Payment Entry")
        payment.payment_type = "Receive"
        payment.party_type = "Customer"
        payment.party = inv.customer
        payment.company = cname
        payment.posting_date = today
        payment.set_posting_time = 1
        payment.paid_amount = inv.outstanding_amount
        payment.received_amount = inv.outstanding_amount
        payment.paid_to = paid_to

        if is_bank:
            payment.reference_no = f"SEED-{company['abbr']}"
            payment.reference_date = today

        payment.append(
            "references",
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": inv.name,
                "allocated_amount": inv.outstanding_amount,
            },
        )
        payment.remarks = SEED_REMARK
        payment.insert()
        payment.submit()
        fixed.append(payment.name)

    print(f"backfilled: {fixed}")
    return {"backfilled": fixed}


def _seed_voucher_names():
    """Collect every seed transaction name, masters excluded."""
    names: set[str] = set()

    specs = [
        ("Payment Entry", {"party": ["like", "Seed Customer%"]}),
        ("Sales Invoice", {"remarks": SEED_REMARK}),
        ("Purchase Invoice", {"remarks": SEED_REMARK}),
        (
            "Sales Order",
            {"customer": ["like", "Seed Customer%"]},
        ),
        (
            "Purchase Order",
            {"supplier": ["like", "Seed Supplier%"]},
        ),
        (
            "Delivery Note",
            {"customer": ["like", "Seed Customer%"]},
        ),
        ("Purchase Receipt", {"remarks": SEED_REMARK}),
    ]

    for doctype, filters in specs:
        for entry in frappe.get_all(doctype, filters=filters):
            names.add(entry.name)

    return names


def orphan_ledger():
    """Show ledger rows still pointing at seed vouchers (wipe gaps)."""

    return _orphan_ledger()


def purge_stale_payments():
    """Remove pre-reseed seed payments one by one, with counts.

    These reference deleted invoices, so their ledger rows must go
    first, then the docs.
    """
    names = [
        row.name
        for row in frappe.get_all(
            "Payment Entry",
            filters={"party": ["like", "Seed Customer%"]},
        )
    ]
    # Only stale ones: anything NOT created by the latest reseed run
    # (latest run payments are tracked via new invoices they allocate).
    removed = []

    for name in sorted(names):
        ple = frappe.db.sql(
            "select name from `tabPayment Ledger Entry` "
            "where voucher_no = %s or against_voucher_no = %s",
            (name, name),
        )
        gle = frappe.db.sql(
            "select name from `tabGL Entry` where voucher_no = %s",
            (name,),
        )

        linked_invoices = frappe.db.sql(
            """select distinct against_voucher_no
            from `tabPayment Ledger Entry`
            where voucher_no = %s
            and against_voucher_type = 'Sales Invoice'""",
            (name,),
        )
        live_links = [
            row[0]
            for row in linked_invoices
            if frappe.db.exists("Sales Invoice", row[0])
        ]

        if live_links:
            print(f"keep {name}: still linked to live {live_links}")
            continue

        frappe.db.sql(
            "delete from `tabPayment Ledger Entry` "
            "where voucher_no = %s or against_voucher_no = %s",
            (name, name),
        )
        frappe.db.sql(
            "delete from `tabGL Entry` where voucher_no = %s",
            (name,),
        )

        doc = frappe.get_doc("Payment Entry", name)

        if doc.docstatus == 1:
            doc.cancel()

        doc.delete()
        removed.append(
            {"name": name, "ple": len(ple), "gl": len(gle)}
        )
        print(f"purged {name}: {len(ple)} PLE + {len(gle)} GL rows")

    return {"removed": removed}


def debug_delete():
    """Empirically test raw DELETE visibility in this environment."""
    name = "ACC-PAY-2026-00006"

    before = frappe.db.sql(
        "select name from `tabPayment Ledger Entry` where voucher_no = %s",
        (name,),
    )
    print("before:", [row[0] for row in before])

    frappe.db.sql(
        "delete from `tabPayment Ledger Entry` where voucher_no = %s",
        (name,),
    )

    after = frappe.db.sql(
        "select name from `tabPayment Ledger Entry` where voucher_no = %s",
        (name,),
    )
    print("after:", [row[0] for row in after])

    frappe.db.rollback()

    restored = frappe.db.sql(
        "select name from `tabPayment Ledger Entry` where voucher_no = %s",
        (name,),
    )
    print("restored:", [row[0] for row in restored])

    return {"before": len(before), "after": len(after)}


def _orphan_ledger():
    names = sorted(_seed_voucher_names())
    ph = ", ".join(["%s"] * len(names))

    out = {}
    out["seed_vouchers"] = len(names)

    for table, column in [
        ("GL Entry", "voucher_no"),
        ("Stock Ledger Entry", "voucher_no"),
    ]:
        rows = frappe.db.sql(
            f"select distinct {column} from `tab{table}` "
            f"where {column} in ({ph})",
            tuple(names),
        )
        out[table] = [row[0] for row in rows]

    out["payment_ledger"] = frappe.db.sql(
        f"""select voucher_type, voucher_no,
        against_voucher_type, against_voucher_no, amount
        from `tabPayment Ledger Entry`
        where voucher_no in ({ph}) or against_voucher_no in ({ph})""",
        tuple(names) + tuple(names),
        as_dict=True,
    )

    print(out)
    return out


def seed_addresses():
    """Give every seed customer a shipping address with a city.

    Picking groups open orders by this city (suburb/town bulk pulls).
    """
    created = []

    for customer in frappe.get_all(
        "Customer", filters={"name": ["like", "Seed Customer%"]}
    ):
        exists = frappe.db.sql(
            """select a.name from tabAddress a
            join `tabDynamic Link` l on l.parent = a.name
            where l.link_doctype = 'Customer'
            and l.link_name = %s limit 1""",
            (customer.name,),
        )

        if exists:
            continue

        territory = frappe.db.get_value(
            "Customer", customer.name, "territory"
        ) or "Johannesburg"

        address = frappe.new_doc("Address")
        address.address_title = customer.name
        address.address_type = "Shipping"
        address.address_line1 = "1 Seed Street"
        address.city = territory
        address.country = "South Africa"
        address.is_primary_address = 1
        address.is_shipping_address = 1
        address.append(
            "links",
            {"link_doctype": "Customer", "link_name": customer.name},
        )
        address.insert()
        created.append(address.name)

    print(f"addresses: {created}")
    return {"addresses": created}


def wipe_seed():
    """Remove all VUMA seed transactions AND their ledger rows.

    Masters (items / customers / suppliers / territories) are kept.
    """
    names = _seed_voucher_names()

    if not names:
        print("wiped: nothing to remove")
        return {}

    placeholders = ", ".join(["%s"] * len(names))
    ordered = tuple(sorted(names))

    stray = frappe.db.sql(
        f"""select distinct voucher_no from `tabPayment Ledger Entry`
        where against_voucher_no in ({placeholders})
        and voucher_no not in ({placeholders})""",
        ordered + ordered,
    )

    if stray:
        raise Exception(
            f"non-seed vouchers reference seed docs, aborting: {stray}"
        )

    frappe.db.sql(
        f"""delete from `tabPayment Ledger Entry`
        where voucher_no in ({placeholders})
        or against_voucher_no in ({placeholders})""",
        ordered + ordered,
    )
    frappe.db.sql(
        f"delete from `tabGL Entry` where voucher_no in ({placeholders})",
        ordered,
    )
    frappe.db.sql(
        f"""delete from `tabStock Ledger Entry`
        where voucher_no in ({placeholders})""",
        ordered,
    )
    frappe.db.sql("delete from tabBin where item_code like 'SEED-%'")

    removed: dict[str, int] = {}

    for doctype in [
        "Payment Entry",
        "Sales Invoice",
        "Purchase Invoice",
        "Sales Order",
        "Purchase Order",
        "Delivery Note",
        "Purchase Receipt",
    ]:
        count = 0

        for name in frappe.get_all(doctype, filters={"name": ["in", ordered]}):
            try:
                doc = frappe.get_doc(doctype, name.name)

                if doc.docstatus == 1:
                    doc.cancel()

                doc.delete()
                count += 1
            except Exception as exc:
                print(f"wipe {doctype} {name.name} failed: {exc}")

        removed[doctype] = count

    print(f"wiped: {removed}")
    return removed


def reseed():
    wipe_seed()
    return run()


def run(months_count=7):
    # Capped to the active fiscal year (Mar 2026 - Feb 2027):
    # backdated vouchers outside it are rejected by ERPNext.
    if frappe.db.count("Sales Invoice", {"remarks": SEED_REMARK}):
        print("VUMA seed already present, skipping.")
        return {"skipped": True}

    today = datetime.date.today()
    months = _month_offsets(today, months_count)

    _ensure_territories()

    item_group = _leaf_group("Item Group", "All Item Groups")
    customer_group = _leaf_group(
        "Customer Group", "All Customer Groups"
    )
    supplier_group = _leaf_group(
        "Supplier Group", "All Supplier Groups"
    )

    report: dict = {"companies": {}}

    for company in COMPANIES:
        cname, abbr = company["name"], company["abbr"]

        if not frappe.db.exists("Company", cname):
            print(f"Company missing, skipping: {cname}")
            continue

        comp = frappe.get_doc("Company", cname)

        if not comp.get("enable_perpetual_inventory"):
            comp.enable_perpetual_inventory = 1
            comp.save()

        warehouse = f"Stores - {abbr}"
        if not frappe.db.exists("Warehouse", warehouse):
            warehouse = comp.get("default_warehouse") or warehouse

        created = {
            "items": [],
            "customers": [],
            "suppliers": [],
            "invoices": [],
            "receipts": [],
            "deliveries": [],
            "bills": [],
            "payments": [],
        }

        # --- items (+ reorder levels so low-stock shows) ---
        reorder_levels = {
            "WIDGET-A": 230,
            "WIDGET-B": 40,
            "GADGET-C": 40,
        }

        for spec in ITEMS:
            code = f"SEED-{abbr}-{spec['suffix']}"

            if frappe.db.exists("Item", code):
                item = frappe.get_doc("Item", code)
            else:
                item = frappe.new_doc("Item")
                item.item_code = code
                item.item_name = f"{spec['name']} ({abbr})"
                item.item_group = item_group
                item.stock_uom = "Nos"
                item.is_stock_item = 1
                item.valuation_method = "FIFO"
                item.append(
                    "item_defaults",
                    {
                        "company": cname,
                        "default_warehouse": warehouse,
                        "income_account": comp.get(
                            "default_income_account"
                        ),
                        "expense_account": comp.get(
                            "default_expense_account"
                        ),
                    },
                )
                item.insert()

            level = reorder_levels[spec["suffix"]]
            has_rule = any(
                row.warehouse == warehouse
                for row in item.get("reorder_levels") or []
            )

            if not has_rule:
                item.append(
                    "reorder_levels",
                    {
                        "warehouse": warehouse,
                        "warehouse_reorder_level": level,
                        "warehouse_reorder_qty": 50,
                        "material_request_type": "Purchase",
                    },
                )
                item.save()

            created["items"].append(code)

        # --- customers / supplier ---
        for idx, territory in enumerate(
            ["Johannesburg", "Cape Town"]
        ):
            ckey = f"Seed Customer {chr(65 + idx)} ({abbr})"

            if not frappe.db.exists("Customer", ckey):
                customer = frappe.new_doc("Customer")
                customer.customer_name = ckey
                customer.customer_group = customer_group
                customer.territory = territory
                customer.insert()

            created["customers"].append(ckey)

        skey = f"Seed Supplier ({abbr})"

        if not frappe.db.exists("Supplier", skey):
            supplier = frappe.new_doc("Supplier")
            supplier.supplier_name = skey
            supplier.supplier_group = supplier_group
            supplier.insert()

        created["suppliers"].append(skey)

        # --- purchase receipts: bring stock in (early + mid) ---
        for month_pos, qty in ((1, 150), (len(months) // 2, 100)):
            month = months[month_pos]
            receipt = frappe.new_doc("Purchase Receipt")
            receipt.supplier = skey
            receipt.company = cname
            receipt.posting_date = _first_day(*month)
            receipt.set_posting_time = 1
            receipt.remarks = SEED_REMARK

            for spec in ITEMS:
                receipt.append(
                    "items",
                    {
                        "item_code": f"SEED-{abbr}-{spec['suffix']}",
                        "qty": qty,
                        "rate": spec["cost"],
                        "warehouse": warehouse,
                    },
                )

            receipt.insert()
            receipt.submit()
            created["receipts"].append(receipt.name)

        # --- delivery notes: ship stock out (posts COGS) ---
        for pos, month in enumerate(months[len(months) // 2 :]):
            delivery = frappe.new_doc("Delivery Note")
            delivery.customer = created["customers"][pos % 2]
            delivery.company = cname
            delivery.posting_date = _first_day(*month)
            delivery.set_posting_time = 1
            delivery.remarks = SEED_REMARK

            for spec in ITEMS[:2]:
                delivery.append(
                    "items",
                    {
                        "item_code": f"SEED-{abbr}-{spec['suffix']}",
                        "qty": 4 + (pos % 3) * 2,
                        "rate": spec["price"],
                        "warehouse": warehouse,
                    },
                )

            delivery.insert()
            delivery.submit()
            created["deliveries"].append(delivery.name)

        # --- sales invoices: monthly through history, varied days ---
        for pos, month in enumerate(months):
            year, mon = month
            day = 4 + (pos * 7) % 24
            posting = datetime.date(year, mon, day)

            invoice = frappe.new_doc("Sales Invoice")
            invoice.customer = created["customers"][pos % 2]
            invoice.company = cname
            invoice.posting_date = posting
            invoice.set_posting_time = 1
            invoice.due_date = posting + datetime.timedelta(days=30)
            invoice.territory = TERRITORIES[pos % 3]
            invoice.remarks = SEED_REMARK

            spec = ITEMS[pos % 3]
            invoice.append(
                "items",
                {
                    "item_code": f"SEED-{abbr}-{spec['suffix']}",
                    "qty": 3 + (pos * 5) % 18,
                    "rate": spec["price"],
                },
            )

            invoice.insert()
            invoice.submit()
            created["invoices"].append(invoice.name)

        # --- purchase invoices: spread over recent months ---
        for month in months[-3:]:
            year, mon = month
            posting = _first_day(year, mon)
            bill = frappe.new_doc("Purchase Invoice")
            bill.supplier = skey
            bill.company = cname
            bill.posting_date = posting
            bill.set_posting_time = 1
            bill.due_date = posting + datetime.timedelta(days=30)
            bill.remarks = SEED_REMARK
            bill.append(
                "items",
                {
                    "item_code": f"SEED-{abbr}-WIDGET-A",
                    "qty": 20,
                    "rate": ITEMS[0]["cost"],
                    "warehouse": warehouse,
                },
            )
            bill.insert()
            bill.submit()
            created["bills"].append(bill.name)

        # --- open sales + purchase orders (order book) ---
        try:
            om_year, om_mon = months[-2]
            order_posting = _first_day(om_year, om_mon)

            so = frappe.new_doc("Sales Order")
            so.customer = created["customers"][0]
            so.company = cname
            so.transaction_date = order_posting
            so.delivery_date = order_posting + datetime.timedelta(
                days=14
            )
            so.remarks = SEED_REMARK
            so.append(
                "items",
                {
                    "item_code": f"SEED-{abbr}-WIDGET-A",
                    "qty": 12,
                    "rate": ITEMS[0]["price"],
                    "delivery_date": order_posting
                    + datetime.timedelta(days=14),
                },
            )
            so.append(
                "items",
                {
                    "item_code": f"SEED-{abbr}-WIDGET-B",
                    "qty": 6,
                    "rate": ITEMS[1]["price"],
                    "delivery_date": order_posting
                    + datetime.timedelta(days=14),
                },
            )
            so.insert()
            so.submit()
            created.setdefault("orders", []).append(so.name)

            po = frappe.new_doc("Purchase Order")
            po.supplier = skey
            po.company = cname
            po.transaction_date = order_posting
            po.schedule_date = order_posting + datetime.timedelta(
                days=14
            )
            po.remarks = SEED_REMARK
            po.append(
                "items",
                {
                    "item_code": f"SEED-{abbr}-WIDGET-A",
                    "qty": 25,
                    "rate": ITEMS[0]["cost"],
                    "warehouse": warehouse,
                    "schedule_date": order_posting
                    + datetime.timedelta(days=14),
                },
            )
            po.insert()
            po.submit()
            created.setdefault("orders", []).append(po.name)
        except Exception as exc:
            created.setdefault("errors", []).append(
                f"orders skipped: {exc}"
            )

        # --- payments against the two oldest invoices ---
        paid_to = comp.get("default_bank_account") or comp.get(
            "default_cash_account"
        )
        is_bank = bool(comp.get("default_bank_account"))

        for invoice_name in created["invoices"][:2]:
            try:
                oldest = frappe.get_doc(
                    "Sales Invoice", invoice_name
                )

                if not (oldest.outstanding_amount or 0) > 0:
                    continue

                payment = frappe.new_doc("Payment Entry")
                payment.payment_type = "Receive"
                payment.party_type = "Customer"
                payment.party = oldest.customer
                payment.company = cname
                payment.posting_date = today
                payment.set_posting_time = 1
                payment.paid_amount = oldest.outstanding_amount
                payment.received_amount = oldest.outstanding_amount
                payment.paid_to = paid_to

                if is_bank:
                    payment.reference_no = f"SEED-{abbr}"
                    payment.reference_date = today

                payment.append(
                    "references",
                    {
                        "reference_doctype": "Sales Invoice",
                        "reference_name": oldest.name,
                        "allocated_amount": oldest.outstanding_amount,
                    },
                )
                payment.remarks = SEED_REMARK
                payment.insert()
                payment.submit()
                created["payments"].append(payment.name)
            except Exception as exc:
                created.setdefault("errors", []).append(
                    f"payment skipped: {exc}"
                )

        report["companies"][cname] = created
        print(f"seeded {cname}: {created}")

    return report
