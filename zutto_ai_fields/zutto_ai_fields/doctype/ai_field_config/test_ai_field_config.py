import frappe
from frappe.tests.utils import FrappeTestCase

class TestAIFieldConfig(FrappeTestCase):
    def tearDown(self):
        # Only clean up test-specific docs created inside this TestCase
        for name in ["User-bio"]:
            if frappe.db.exists("AI Field Config", name):
                frappe.delete_doc("AI Field Config", name, force=1)
        frappe.db.commit()

    def test_composite_autoname(self):
        doc = frappe.get_doc({
            "doctype": "AI Field Config",
            "enabled": 1,
            "target_doctype": "User",
            "target_field": "bio",
            "prompt_template": "Write bio for {{first_name}}"
        }).insert()

        self.assertEqual(doc.name, "User-bio")

    def test_all_supported_fieldtypes(self):
        test_cases = [
            ("User", "first_name", "Data"),
            ("Event", "subject", "Small Text"),
            ("ToDo", "description", "Text Editor"),
            ("Event", "event_category", "Select"),
            ("Event", "all_day", "Check"),
            ("ToDo", "date", "Date"),
            ("Event", "starts_on", "Datetime"),
            ("User", "simultaneous_sessions", "Int"),
            ("User", "language", "Link"),
            ("ToDo", "reference_name", "Dynamic Link"),
            ("Event", "event_participants", "Table"),
            ("User Group", "user_group_members", "Table MultiSelect"),
            ("Print Format", "margin_top", "Float"),
            ("Currency", "smallest_currency_fraction_value", "Currency"),
            ("User", "home_settings", "Code")
        ]

        for doctype, field, expected_type in test_cases:
            cfg = frappe.new_doc("AI Field Config")
            cfg.target_doctype = doctype
            cfg.target_field = field
            cfg.prompt_template = f"Generate {expected_type} content"
            try:
                cfg.validate()
            except Exception as e:
                self.fail(f"Field {doctype}.{field} ({expected_type}) validation failed unexpectedly: {e}")

    def test_prohibited_layout_and_attachment_fieldtypes(self):
        prohibited = [
            ("User", "sb1", "Section Break"),
            ("User", "column_break0", "Column Break"),
            ("User", "settings_tab", "Tab Break"),
            ("User", "user_image", "Attach Image")
        ]

        for doctype, field, fieldtype in prohibited:
            cfg = frappe.new_doc("AI Field Config")
            cfg.target_doctype = doctype
            cfg.target_field = field
            cfg.prompt_template = "Generate break"
            with self.assertRaises(frappe.ValidationError, msg=f"Expected rejection for {fieldtype}"):
                cfg.validate()

    def test_nonexistent_field_validation(self):
        cfg = frappe.new_doc("AI Field Config")
        cfg.target_doctype = "User"
        cfg.target_field = "field_that_does_not_exist_abc"
        cfg.prompt_template = "Test prompt"
        with self.assertRaises(frappe.ValidationError):
            cfg.validate()

    def test_placeholder_helpers(self):
        cfg = frappe.new_doc("AI Field Config")
        cfg.target_doctype = "User"
        cfg.target_field = "bio"
        cfg.prompt_template = "Hello {{first_name}} {{last_name}}, role {{role}}"

        help_html = cfg.get_placeholder_help()
        self.assertIn("first_name", help_html)
        self.assertIn("last_name", help_html)

        preview = cfg.get_preview_html()
        self.assertIn("Hello", preview)
