
from __future__ import annotations

import datetime

import frappe

from vuma.api.v1.responses import success


PERIOD_MONTHS = 12


def _month_starts(today, count):
    year, month = today.year, today.month
    starts = []

    for _ in range(count):
        starts.append(datetime.date(year, month, 1))

        month -= 1

        if month == 0:
            month, year = 12, year - 1

    return list(reversed(starts))


def _month_label(year, month):
    return datetime.date(year, month, 1).strftime("%b %y")


def _safe_float(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _validated_company(company):
    company = str(company or "").strip()

    if not company:
        return None

    if not frappe.db.exists("Company", company):
        return None

    return company


@frappe.whitelist()
def check():
    """Compact probe of the summary (debugging)."""
    data = summary()["data"]

    return {
        "currency": data["currency"],
        "multi_company": data["multi_company"],
        "period_months": data["period_months"],
        "sales_this_month": data["sales_this_month"],
        "sales_last_month": data["sales_last_month"],
        "cost_this_month": data["cost_this_month"],
        "receivables": data["receivables"],
        "payables": data["payables"],
        "overdue_receivables": data["overdue_receivables"],
        "overdue_payables": data["overdue_payables"],
        "inventory_total": data["inventory_total"],
        "warehouse_count": data["warehouse_count"],
        "companies": data["companies"],
        "monthly_sales": data["monthly_sales"],
        "monthly_cost": data["monthly_cost"],
        "company_performance": data["company_performance"],
        "top_items_by_company": data["top_items_by_company"],
        "low_stock": data["low_stock"],
        "top_customers": data["top_customers"],
        "sales_by_territory": data["sales_by_territory"],
        "inventory_by_warehouse": data["inventory_by_warehouse"][:4],
        "open_sales_orders": data["open_sales_orders"],
        "open_purchase_orders": data["open_purchase_orders"],
    }


@frappe.whitelist()
def summary(company=None):
    co = _validated_company(company)
    today = datetime.date.today()
    starts = _month_starts(today, PERIOD_MONTHS)
    start_date = starts[0]

    data = {
        "generated_on": today.isoformat(),
        "period_months": PERIOD_MONTHS,
        "currency": "",
        "multi_company": False,
        "companies": [],
        "monthly_sales": [],
        "monthly_cost": [],
        "sales_this_month": 0.0,
        "sales_last_month": 0.0,
        "cost_this_month": 0.0,
        "receivables": 0.0,
        "payables": 0.0,
        "inventory_total": 0.0,
        "warehouse_count": 0,
        "inventory_by_warehouse": [],
        "sales_by_territory": [],
        "top_items_by_company": [],
        "low_stock": [],
        "top_customers": [],
        "company_performance": [],
        "overdue_receivables": 0.0,
        "overdue_receivable_count": 0,
        "overdue_payables": 0.0,
        "overdue_bill_count": 0,
        "open_sales_orders": {"count": 0, "value": 0.0},
        "open_purchase_orders": {"count": 0, "value": 0.0},
    }

    try:
        companies = frappe.db.sql(
            "select name, default_currency from tabCompany order by name limit 50",
            as_dict=True,
        )
    except Exception:
        companies = []

    # --- sales invoices: monthly trend, by company, by territory ---
    try:
        params: list = [start_date]

        if co:
            params.append(co)

        rows = frappe.db.sql(
            """
            select company, customer, territory, posting_date, base_grand_total
            from `tabSales Invoice`
            where docstatus = 1 and posting_date >= %s
            """
            + (" and company = %s" if co else ""),
            tuple(params),
            as_dict=True,
        )
    except Exception:
        rows = []

    month_index = {
        (start.year, start.month): position
        for position, start in enumerate(starts)
    }

    monthly_sales = [0.0] * PERIOD_MONTHS
    by_company: dict[str, float] = {}
    by_territory: dict[str, float] = {}
    by_customer: dict[str, float] = {}

    for row in rows:
        total = _safe_float(row.get("base_grand_total"))
        posting = row.get("posting_date")

        if hasattr(posting, "year"):
            position = month_index.get((posting.year, posting.month))

            if position is not None:
                monthly_sales[position] += total

        company = (row.get("company") or "Unspecified").strip() or "Unspecified"
        by_company[company] = by_company.get(company, 0.0) + total

        customer = (row.get("customer") or "").strip()

        if customer:
            by_customer[customer] = by_customer.get(customer, 0.0) + total

        territory = (row.get("territory") or "").strip()

        if territory:
            by_territory[territory] = by_territory.get(territory, 0.0) + total

    data["monthly_sales"] = [
        {
            "month": f"{start.year:04d}-{start.month:02d}",
            "label": _month_label(start.year, start.month),
            "total": round(monthly_sales[position], 2),
        }
        for position, start in enumerate(starts)
    ]

    data["sales_this_month"] = round(monthly_sales[-1], 2)
    data["sales_last_month"] = (
        round(monthly_sales[-2], 2) if PERIOD_MONTHS > 1 else 0.0
    )

    data["companies"] = [
        {
            "name": company.get("name"),
            "currency": company.get("default_currency") or "",
            "sales": round(by_company.get(company.get("name"), 0.0), 2),
        }
        for company in companies
    ]

    for company, total in sorted(
        by_company.items(), key=lambda item: item[1], reverse=True
    ):
        if not any(entry["name"] == company for entry in data["companies"]):
            data["companies"].append(
                {"name": company, "currency": "", "sales": round(total, 2)}
            )

    data["multi_company"] = len(data["companies"]) > 1

    if data["companies"]:
        ranked = sorted(
            data["companies"], key=lambda entry: entry["sales"], reverse=True
        )

        data["currency"] = ranked[0].get("currency") or ""

    data["sales_by_territory"] = [
        {"territory": territory, "total": round(total, 2)}
        for territory, total in sorted(
            by_territory.items(), key=lambda item: item[1], reverse=True
        )[:10]
    ]

    data["top_customers"] = [
        {"customer": customer, "total": round(total, 2)}
        for customer, total in sorted(
            by_customer.items(), key=lambda item: item[1], reverse=True
        )[:5]
    ]

    # --- best / slowest sellers per company (invoiced qty + revenue) ---
    try:
        params = [start_date]

        if co:
            params.append(co)

        item_rows = frappe.db.sql(
            """
            select p.company, i.item_code, i.item_name,
                   sum(i.qty) as qty, sum(i.base_net_amount) as revenue
            from `tabSales Invoice Item` i
            join `tabSales Invoice` p on p.name = i.parent
            where p.docstatus = 1 and p.posting_date >= %s
            """
            + (" and p.company = %s" if co else "")
            + """
            group by p.company, i.item_code, i.item_name
            """,
            tuple(params),
            as_dict=True,
        )
    except Exception:
        item_rows = []

    grouped: dict[str, list] = {}

    for row in item_rows:
        company = (row.get("company") or "Unspecified").strip()

        grouped.setdefault(company, []).append(
            {
                "item_code": row.get("item_code"),
                "item_name": row.get("item_name")
                or row.get("item_code"),
                "qty": round(_safe_float(row.get("qty")), 2),
                "revenue": round(_safe_float(row.get("revenue")), 2),
            }
        )

    data["top_items_by_company"] = [
        {
            "company": company,
            "top": sorted(
                items, key=lambda e: e["qty"], reverse=True
            )[:3],
            "bottom": sorted(items, key=lambda e: e["qty"])[:3],
        }
        for company, items in sorted(grouped.items())
    ]

    # --- cost of sales from the ledger (COGS accounts, incl. children) ---
    try:
        roots = frappe.db.sql(
            "select name, company, lft, rgt from tabAccount "
            "where account_type = 'Cost of Goods Sold'",
            as_dict=True,
        )

        cogs_accounts: set[str] = set()

        for root in roots:
            cogs_accounts.add(root.get("name"))

            children = frappe.db.sql(
                "select name from tabAccount "
                "where company = %s and lft >= %s and rgt <= %s",
                (
                    root.get("company"),
                    root.get("lft"),
                    root.get("rgt"),
                ),
                as_dict=True,
            )

            for child in children:
                cogs_accounts.add(child.get("name"))

        monthly_cost = [0.0] * PERIOD_MONTHS
        by_company_cost: dict[str, float] = {}

        if cogs_accounts:
            placeholders = ", ".join(["%s"] * len(cogs_accounts))
            gl_params: list = [start_date, *sorted(cogs_accounts)]

            if co:
                gl_params.append(co)

            gl_rows = frappe.db.sql(
                f"""
                select posting_date, company, debit, credit
                from `tabGL Entry`
                where is_cancelled = 0 and posting_date >= %s
                and account in ({placeholders})
                """
                + (" and company = %s" if co else ""),
                tuple(gl_params),
                as_dict=True,
            )

            for row in gl_rows:
                net = _safe_float(row.get("debit")) - _safe_float(
                    row.get("credit")
                )
                posting = row.get("posting_date")

                if hasattr(posting, "year"):
                    position = month_index.get(
                        (posting.year, posting.month)
                    )

                    if position is not None:
                        monthly_cost[position] += net

                company = (row.get("company") or "").strip()

                if company:
                    by_company_cost[company] = (
                        by_company_cost.get(company, 0.0) + net
                    )

        data["monthly_cost"] = [
            {
                "month": f"{start.year:04d}-{start.month:02d}",
                "label": _month_label(start.year, start.month),
                "total": round(monthly_cost[position], 2),
            }
            for position, start in enumerate(starts)
        ]

        data["cost_this_month"] = round(monthly_cost[-1], 2)

        performance = []

        for entry in data["companies"]:
            if co and entry["name"] != co:
                continue

            sales = entry["sales"]
            cost = round(by_company_cost.get(entry["name"], 0.0), 2)
            profit = round(sales - cost, 2)

            performance.append(
                {
                    "name": entry["name"],
                    "currency": entry["currency"],
                    "sales": sales,
                    "cost": cost,
                    "profit": profit,
                    "margin": round(profit / sales * 100, 1)
                    if sales > 0
                    else None,
                }
            )

        performance.sort(key=lambda e: e["profit"], reverse=True)

        data["company_performance"] = performance
    except Exception:
        pass

    # --- receivables / payables (open balances, all time) ---
    try:
        rows = frappe.db.sql(
            "select sum(outstanding_amount) as total "
            "from `tabSales Invoice` "
            "where docstatus = 1 and outstanding_amount > 0"
            + (" and company = %s" if co else ""),
            tuple([co] if co else []),
            as_dict=True,
        )

        data["receivables"] = round(
            _safe_float((rows or [{}])[0].get("total")), 2
        )
    except Exception:
        pass

    try:
        rows = frappe.db.sql(
            "select sum(outstanding_amount) as total, count(*) as count "
            "from `tabSales Invoice` "
            "where docstatus = 1 and outstanding_amount > 0 "
            "and due_date < %s"
            + (" and company = %s" if co else ""),
            tuple([today] + ([co] if co else [])),
            as_dict=True,
        )

        data["overdue_receivables"] = round(
            _safe_float((rows or [{}])[0].get("total")), 2
        )
        data["overdue_receivable_count"] = int(
            (rows or [{}])[0].get("count") or 0
        )
    except Exception:
        pass

    try:
        rows = frappe.db.sql(
            "select sum(outstanding_amount) as total "
            "from `tabPurchase Invoice` "
            "where docstatus = 1 and outstanding_amount > 0"
            + (" and company = %s" if co else ""),
            tuple([co] if co else []),
            as_dict=True,
        )

        data["payables"] = round(
            _safe_float((rows or [{}])[0].get("total")), 2
        )
    except Exception:
        pass

    try:
        rows = frappe.db.sql(
            "select sum(outstanding_amount) as total, count(*) as count "
            "from `tabPurchase Invoice` "
            "where docstatus = 1 and outstanding_amount > 0 "
            "and due_date < %s"
            + (" and company = %s" if co else ""),
            tuple([today] + ([co] if co else [])),
            as_dict=True,
        )

        data["overdue_payables"] = round(
            _safe_float((rows or [{}])[0].get("total")), 2
        )
        data["overdue_bill_count"] = int(
            (rows or [{}])[0].get("count") or 0
        )
    except Exception:
        pass

    # --- open order book ---
    for key, table in (
        ("open_sales_orders", "Sales Order"),
        ("open_purchase_orders", "Purchase Order"),
    ):
        try:
            rows = frappe.db.sql(
                f"""select count(*) as count, sum(base_grand_total) as total
                from `tab{table}`
                where docstatus = 1
                and status not in ('Completed', 'Closed', 'Cancelled')"""
                + (" and company = %s" if co else ""),
                tuple([co] if co else []),
                as_dict=True,
            )

            data[key] = {
                "count": int((rows or [{}])[0].get("count") or 0),
                "value": round(
                    _safe_float((rows or [{}])[0].get("total")), 2
                ),
            }
        except Exception:
            pass

    # --- group inventory from bins ---
    try:
        bins = frappe.db.sql(
            "select warehouse, company, "
            "sum(stock_value) as `value`, count(*) as `lines` "
            "from `tabBin`"
            + (" where company = %s" if co else "")
            + " group by warehouse, company "
            "order by `value` desc limit 50",
            tuple([co] if co else []),
            as_dict=True,
        )

        total = 0.0
        warehouses = set()
        breakdown = []

        for row in bins:
            value = _safe_float(row.get("value"))
            total += value

            warehouse = row.get("warehouse") or "Unspecified"
            warehouses.add(warehouse)

            breakdown.append(
                {
                    "warehouse": warehouse,
                    "company": row.get("company") or "",
                    "value": round(value, 2),
                }
            )

        breakdown.sort(key=lambda entry: entry["value"], reverse=True)

        data["inventory_total"] = round(total, 2)
        data["warehouse_count"] = len(warehouses)
        data["inventory_by_warehouse"] = breakdown[:10]
    except Exception:
        pass

    # --- stock running low (reorder breaches + managed stockouts) ---
    try:
        rows = frappe.db.sql(
            """select b.item_code, i.item_name, b.warehouse, b.company,
            b.actual_qty, r.warehouse_reorder_level as level
            from tabBin b
            join tabItem i on i.name = b.item_code
            left join `tabItem Reorder` r
              on r.parent = b.item_code and r.warehouse = b.warehouse
            where ((r.warehouse_reorder_level is not null
                   and b.actual_qty <= r.warehouse_reorder_level)
               or (b.actual_qty <= 0
                   and exists (select 1 from `tabItem Reorder` r2
                               where r2.parent = b.item_code)))"""
            + (" and b.company = %s" if co else "")
            + """
            order by (b.actual_qty - coalesce(r.warehouse_reorder_level, 0))
            asc limit 10""",
            tuple([co] if co else []),
            as_dict=True,
        )

        data["low_stock"] = [
            {
                "item_code": row.get("item_code"),
                "item_name": row.get("item_name")
                or row.get("item_code"),
                "warehouse": row.get("warehouse"),
                "company": row.get("company") or "",
                "qty": _safe_float(row.get("actual_qty")),
                "reorder_level": _safe_float(row.get("level")),
            }
            for row in rows
        ]
    except Exception:
        pass

    return success(data=data)
