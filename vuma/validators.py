"""Cross-cutting document validations for the Vuma app."""

from __future__ import annotations

import frappe
from frappe import _


def validate_company_tax(doc):
    """Require a VAT number when the company is VAT registered."""
    is_registered = bool(doc.get("is_vat_registered"))

    tax_id = str(doc.get("tax_id") or "").strip()

    if tax_id:
        doc.tax_id = tax_id

    if is_registered and not tax_id:
        frappe.throw(
            _(
                "VAT Registration Number (Tax ID) is required "
                "when VAT Registered is checked for {0}."
            ).format(doc.get("company_name") or doc.get("name") or "Company")
        )
