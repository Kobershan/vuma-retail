import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class VumaDeviceActivation(Document):
    def before_insert(self):
        if not self.created_by_user:
            self.created_by_user = frappe.session.user

    def validate(self):
        if self.status == "Pending" and self.expires_at:
            if self.expires_at < now_datetime():
                self.status = "Expired"
