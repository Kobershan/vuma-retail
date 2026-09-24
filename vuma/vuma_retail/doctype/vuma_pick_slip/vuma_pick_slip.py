from frappe.model.document import Document
from frappe.model.naming import make_autoname


class VumaPickSlip(Document):
    def before_insert(self):
        if not self.slip_id:
            self.slip_id = make_autoname("VPS-.#####")

