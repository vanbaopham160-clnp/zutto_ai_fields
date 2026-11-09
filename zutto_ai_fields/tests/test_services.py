from unittest.mock import patch, MagicMock
import frappe
from frappe.tests.utils import FrappeTestCase
from zutto_ai_fields.services.prompt_service import (
    build_prompt,
    validate_placeholders,
    extract_placeholders,
    get_placeholder_suggestions
)
from zutto_ai_fields.services.llm_service import (
    get_provider_instance,
    resolve_provider_and_model,
    execute_generation
)
from zutto_ai_fields.services.providers.base import LLMResponse
from zutto_ai_fields.services.providers.custom_provider import CustomProvider
from zutto_ai_fields.api import (
    get_ai_field_configs,
    generate_content,
    test_provider_connection,
    test_ai_field_config
)

class TestServicesAndAPI(FrappeTestCase):
    def setUp(self):
        for name in ["Test-Claude", "Test-OpenAI", "Test-QwenPlan", "Test-MiMoPlan", "Test-Custom"]:
            if frappe.db.exists("Zutto AI Provider", name):
                frappe.delete_doc("Zutto AI Provider", name, force=1)
        for cfg in ["User-bio", "ToDo-color"]:
            if frappe.db.exists("AI Field Config", cfg):
                frappe.delete_doc("AI Field Config", cfg, force=1)
        frappe.db.commit()

    def tearDown(self):
        for name in ["Test-Claude", "Test-OpenAI", "Test-QwenPlan", "Test-MiMoPlan", "Test-Custom"]:
            if frappe.db.exists("Zutto AI Provider", name):
                frappe.delete_doc("Zutto AI Provider", name, force=1)
        for cfg in ["User-bio", "ToDo-color"]:
            if frappe.db.exists("AI Field Config", cfg):
                frappe.delete_doc("AI Field Config", cfg, force=1)
        frappe.db.commit()

    def test_extract_and_build_prompt(self):
        template = "User {{user_name}} placed order {{order_id}} with status {{status}} and notes {{doc.notes}}."
        tokens = extract_placeholders(template)
        self.assertEqual(tokens, ["user_name", "order_id", "status", "notes"])

        doc = {"user_name": "Alice", "order_id": 404, "status": None, "notes": "Deliver fast"}
        result = build_prompt(template, doc)
        self.assertEqual(result, "User Alice placed order 404 with status  and notes Deliver fast.")

        is_valid, missing = validate_placeholders(template, {"user_name": "Bob"})
        self.assertFalse(is_valid)
        self.assertIn("order_id", missing)
        self.assertIn("status", missing)
        self.assertIn("notes", missing)

    def test_qwen_and_mimo_plan_default_endpoints(self):
        qwen = get_provider_instance("Qwen (Token Plan)", api_key="sk-sp-test")
        self.assertEqual(qwen.config.get("base_url"), "https://token-plan.maas.qwencloudapi.com/compatible-mode/v1")
        self.assertEqual(qwen.config.get("model"), "qwen3.7-max")

        mimo = get_provider_instance("MiMo (Token Plan)", api_key="tp-test")
        self.assertEqual(mimo.config.get("base_url"), "https://token-plan-cn.xiaomimimo.com/v1")
        self.assertEqual(mimo.config.get("model"), "mimo-v2.5-pro")

    def test_custom_provider_bearer_and_url_cleanup(self):
        provider = CustomProvider(
            api_key="   Bearer  my-secret-key   ",
            config={"base_url": "https://my-ollama-host:11434/v1/"}
        )

        with patch("requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "Paris"}}]}
            )

            res = provider.generate("What is capital of France?")
            self.assertTrue(res.success)
            self.assertEqual(res.content, "Paris")

            # Check that requests.post was called with cleaned endpoint and Bearer
            called_args, called_kwargs = mock_post.call_args
            self.assertEqual(called_args[0], "https://my-ollama-host:11434/v1/chat/completions")
            self.assertEqual(called_kwargs["headers"]["Authorization"], "Bearer my-secret-key")

    def test_resolution_engine_precedence(self):
        # 1. Default provider
        frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Claude",
            "provider": "Anthropic (Claude)",
            "api_key": "sk-ant",
            "default_chat_model": "claude-sonnet-5-5",
            "default_provider": 1,
            "active": 1
        }).insert()

        # 2. Alternative provider
        frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-OpenAI",
            "provider": "OpenAI (ChatGPT)",
            "api_key": "sk-oai",
            "default_chat_model": "gpt-5-mini",
            "default_provider": 0,
            "active": 1
        }).insert()

        # Resolution without override -> uses default provider
        prov, model = resolve_provider_and_model({"override_provider": 0})
        self.assertEqual(prov.name, "Test-Claude")
        self.assertEqual(model, "claude-sonnet-5-5")

        # Resolution with override -> uses specified provider and model
        prov, model = resolve_provider_and_model({
            "override_provider": 1,
            "provider": "Test-OpenAI",
            "model": "gpt-4o"
        })
        self.assertEqual(prov.name, "Test-OpenAI")
        self.assertEqual(model, "gpt-4o")

    def test_get_ai_field_configs_rpc(self):
        frappe.get_doc({
            "doctype": "AI Field Config",
            "enabled": 1,
            "target_doctype": "User",
            "target_field": "bio",
            "prompt_template": "Write bio for {{email}}"
        }).insert()

        configs = get_ai_field_configs("User")
        fieldnames = [c["target_field"] for c in configs]
        self.assertIn("bio", fieldnames)

    @patch("zutto_ai_fields.api.execute_generation")
    def test_generate_content_api_success(self, mock_exec):
        mock_exec.return_value = LLMResponse(success=True, content="Simulated AI description")

        frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Claude",
            "provider": "Anthropic (Claude)",
            "api_key": "sk-ant",
            "default_chat_model": "claude-sonnet-5-5",
            "default_provider": 1,
            "active": 1
        }).insert()

        frappe.get_doc({
            "doctype": "AI Field Config",
            "enabled": 1,
            "target_doctype": "ToDo",
            "target_field": "color",
            "prompt_template": "Task details for {{sender}}"
        }).insert()

        res = generate_content("ToDo-color", {"sender": "Alice"})
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("content"), "Simulated AI description")
        self.assertEqual(res.get("provider"), "Test-Claude")

    def test_generate_content_not_found(self):
        res = generate_content("NonExistent-field", {})
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error_type"), "not_found")

    @patch("zutto_ai_fields.api.execute_generation")
    def test_test_provider_connection_api(self, mock_exec):
        mock_exec.return_value = LLMResponse(success=True, content="Connection successful!")

        frappe.get_doc({
            "doctype": "Zutto AI Provider",
            "provider_name": "Test-Claude",
            "provider": "Anthropic (Claude)",
            "api_key": "sk-ant",
            "default_chat_model": "claude-sonnet-5-5",
            "active": 1
        }).insert()

        res = test_provider_connection("Test-Claude")
        self.assertTrue(res.get("success"))
        self.assertIn("Connection successful!", res.get("message"))

        res_missing = test_provider_connection("Does-Not-Exist")
        self.assertFalse(res_missing.get("success"))
