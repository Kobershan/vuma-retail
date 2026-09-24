import frappe
from frappe.model.document import Document


class VumaInstallationModule(Document):
    def validate(self):
        duplicate = frappe.db.exists(
            "Vuma Installation Module",
            {
                "installation": self.installation,
                "module": self.module,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                f"{self.module} is already linked to installation {self.installation}."
            )
