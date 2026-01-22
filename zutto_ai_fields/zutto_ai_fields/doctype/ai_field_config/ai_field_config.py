import frappe
from frappe.model.document import Document
from frappe import _

class AIFieldConfig(Document):
    """AI Field Configuration - Defines which fields can be auto-generated"""

    def validate(self):
        """Validate configuration before save"""
        # Validate target field exists in target doctype
        if self.target_doctype and self.target_field:
            try:
                meta = frappe.get_meta(self.target_doctype)
                field = meta.get_field(self.target_field)

                if not field:
                    frappe.throw(_(
                        "Field '{0}' does not exist in DocType '{1}'"
                    ).format(self.target_field, self.target_doctype))

                # Check if field is valid for AI generation
                if field.fieldtype not in ["Text", "Text Editor", "Data", "Small Text", "Code"]:
                    frappe.msgprint(_(
                        "Warning: Field type '{0}' may not be optimal for AI generation. "
                        "Text-based fields work best."
                    ).format(field.fieldtype))

            except Exception:
                frappe.throw(_(
                    "Could not validate field '{0}' in DocType '{1}'"
                ).format(self.target_field, self.target_doctype))

        # Validate prompt template
        if self.prompt_template:
            from zutto_ai_fields.services.prompt_service import get_placeholder_suggestions

            placeholders = get_placeholder_suggestions(self.prompt_template)

            if not placeholders:
                frappe.msgprint(_(
                    "No placeholders found in prompt template. "
                    "Use {{field_name}} to reference document fields."
                ))

    def get_placeholder_help(self):
        """Generate HTML help for placeholders"""
        if not self.prompt_template:
            return ""

        from zutto_ai_fields.services.prompt_service import get_placeholder_suggestions

        placeholders = get_placeholder_suggestions(self.prompt_template)

        if not placeholders:
            return ""

        # Get available fields from target doctype
        available_fields = []
        if self.target_doctype:
            try:
                meta = frappe.get_meta(self.target_doctype)
                available_fields = [f.fieldname for f in meta.fields]
            except:
                pass

        html = "<div style='margin-top: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px;'>"
        html += "<strong>Placeholders found:</strong><br>"

        for placeholder in placeholders:
            status = "✓" if placeholder in available_fields else "✗"
            color = "green" if placeholder in available_fields else "red"
            html += f"<span style='color: {color};'>{status} {{{{placeholder}}}}</span><br>"

        html += "</div>"
        return html

    def get_preview_html(self):
        """Generate preview HTML"""
        if not self.prompt_template:
            return ""

        preview_text = self.prompt_template[:200]
        if len(self.prompt_template) > 200:
            preview_text += "..."

        html = f"""
        <div style='margin-top: 10px; padding: 10px; background: #f0f8ff; border-radius: 5px; font-family: monospace; font-size: 12px;'>
            <strong>Preview:</strong><br>
            {frappe.utils.escape_html(preview_text)}
        </div>
        """
        return html

    @frappe.whitelist()
    def test_generation(self):
        """Test generation with sample data"""
        from zutto_ai_fields.api import generate_content
        from zutto_ai_fields.services.prompt_service import get_placeholder_suggestions

        if not self.enabled:
            return {"success": False, "error": "Config is disabled"}

        if not self.prompt_template:
            return {"success": False, "error": "Prompt template is required"}

        # Get placeholders
        placeholders = get_placeholder_suggestions(self.prompt_template)

        # Create sample doc with placeholder values
        sample_doc = {}
        for placeholder in placeholders:
            sample_doc[placeholder] = f"[Sample {placeholder}]"

        # Use current document if available
        if self.target_doctype and self.target_field:
            # Try to get a sample document
            try:
                sample_records = frappe.get_all(
                    self.target_doctype,
                    limit=1,
                    pluck="name"
                )
                if sample_records:
                    sample_doc = frappe.get_value(
                        self.target_doctype,
                        sample_records[0],
                        "*",
                        as_dict=True
                    )
            except:
                pass

        # Generate
        try:
            response = generate_content(
                config_name=self.name,
                doc=sample_doc
            )

            if response.get("success"):
                return {
                    "success": True,
                    "message": f"Test successful! Generated content:\n\n{response.get('content')[:500]}...",
                    "provider": response.get("provider"),
                    "model": response.get("model")
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error")
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Test generation failed: {str(e)}"
            }