import hashlib

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class VumaDevice(Document):
    def before_insert(self):
        if not self.registered_at:
            self.registered_at = now_datetime()

    def validate(self):
        self._validate_build()
        self._set_public_key_fingerprint()
        self._validate_duplicate_public_key()

        if self.status == "Revoked" and not self.revoked_at:
            self.revoked_at = now_datetime()
            self.revoked_by = frappe.session.user

    def _validate_build(self):
        build = frappe.get_doc("Vuma Build", self.build)

        if build.blocked:
            frappe.throw(
                _("Build {0} has been blocked.").format(build.build_id)
            )

        if not build.active:
            frappe.throw(
                _("Build {0} is not active.").format(build.build_id)
            )

        if build.platform != self.platform:
            frappe.throw(
                _(
                    "Build platform {0} does not match device platform {1}."
                ).format(build.platform, self.platform)
            )

    def _set_public_key_fingerprint(self):
        public_key = (self.public_key or "").strip()

        if not public_key:
            return

        self.public_key_fingerprint = hashlib.sha256(
            public_key.encode("utf-8")
        ).hexdigest()

    def _validate_duplicate_public_key(self):
        if not self.public_key_fingerprint:
            return

        duplicate = frappe.db.exists(
            "Vuma Device",
            {
                "public_key_fingerprint": self.public_key_fingerprint,
                "name": ["!=", self.name],
            },
        )

        if duplicate:
            frappe.throw(
                _("This cryptographic device identity is already registered.")
            )
