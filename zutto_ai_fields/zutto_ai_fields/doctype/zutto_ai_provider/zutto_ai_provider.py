import frappe
from frappe import _
from frappe.model.document import Document

class ZuttoAIProvider(Document):
    def validate(self):
        # Validate that default provider must be active
        if self.default_provider:
            if not self.active:
                frappe.throw(_("A default provider must be active."))

            # Reset default_provider flag on all other providers
            frappe.db.sql(
                """
                UPDATE `tabZutto AI Provider`
                SET default_provider = 0
                WHERE name != %s
                """,
                (self.name,),
            )

    def get_api_key(self) -> str:
        """Safely retrieve the decrypted and cleaned API key"""
        raw_key = (self.get_password("api_key") or "").strip()
        if raw_key.lower().startswith("bearer "):
            raw_key = raw_key[7:].strip()
        return raw_key
