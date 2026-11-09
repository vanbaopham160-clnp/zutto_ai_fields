import frappe
from frappe.tests.utils import FrappeTestCase

class TestZuttoAIProvider(FrappeTestCase):
    def tearDown(self):
        for name in ["Test-Provider-A", "Test-Provider-B", "Test-Provider-Long"]:
            if frappe.db.exists("Zutto AI Provider", name):
                frappe.delete_doc("Zutto AI Provider", name, force=1)
        frappe.db.commit()

    def test_create_provider_defaults(self):
        doc = frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Provider-A",
            "provider": "Anthropic (Claude)",
            "api_key": "sk-ant-test",
            "default_chat_model": "claude-sonnet-5-5"
        }).insert()

        self.assertEqual(doc.max_tokens, 1000)
        self.assertEqual(doc.request_timeout, 30)
        self.assertEqual(doc.active, 1)
        self.assertEqual(doc.default_provider, 0)

    def test_single_default_provider_invariant(self):
        doc_a = frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Provider-A",
            "provider": "Anthropic (Claude)",
            "api_key": "key-a",
            "default_chat_model": "claude-sonnet-5-5",
            "default_provider": 1,
            "active": 1
        }).insert()
        self.assertEqual(doc_a.default_provider, 1)

        doc_b = frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Provider-B",
            "provider": "OpenAI (ChatGPT)",
            "api_key": "key-b",
            "default_chat_model": "gpt-5-mini",
            "default_provider": 1,
            "active": 1
        }).insert()
        self.assertEqual(doc_b.default_provider, 1)

        doc_a.reload()
        self.assertEqual(doc_a.default_provider, 0, "Provider A should have been reset to default_provider=0")

    def test_default_provider_must_be_active(self):
        doc = frappe.new_doc("Zutto AI Provider")
        doc.provider_name = "Test-Provider-A"
        doc.provider = "Anthropic (Claude)"
        doc.default_chat_model = "claude-sonnet-5-5"
        doc.default_provider = 1
        doc.active = 0

        self.assertRaises(frappe.ValidationError, doc.save)

    def test_api_key_encryption_and_cleaning(self):
        doc = frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Provider-A",
            "provider": "OpenAI (ChatGPT)",
            "api_key": "   Bearer sk-test-key-clean   ",
            "default_chat_model": "gpt-5-mini",
            "active": 1
        }).insert()

        cleaned_key = doc.get_api_key()
        self.assertEqual(cleaned_key, "sk-test-key-clean", "get_api_key() should strip whitespace and 'Bearer ' prefix")

    def test_long_api_key_storage(self):
        long_key = "sk-" + "x" * 250
        doc = frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Provider-Long",
            "provider": "Custom / Ollama",
            "api_key": long_key,
            "default_chat_model": "llama3",
            "active": 1
        }).insert()

        self.assertEqual(doc.get_api_key(), long_key, "250+ character key should be saved and retrieved intact")
