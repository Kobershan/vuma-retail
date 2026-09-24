import frappe
from frappe.model.document import Document


class VumaCompanyLocation(Document):
    def validate(self):
        duplicate = frappe.db.exists(
            "Vuma Company Location",
            {
                "company": self.company,
                "location": self.location,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                f"{self.company} is already linked to {self.location}."
            )
