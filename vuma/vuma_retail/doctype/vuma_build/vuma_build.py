import frappe
from frappe import _
from frappe.model.document import Document


class VumaBuild(Document):
    def validate(self):
        if self.blocked:
            self.active = 0

        duplicate = frappe.db.exists(
            "Vuma Build",
            {
                "build_id": self.build_id,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("Build ID {0} already exists.").format(self.build_id)
            )
