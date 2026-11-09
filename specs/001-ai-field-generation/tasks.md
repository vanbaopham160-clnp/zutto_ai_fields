# Tasks: AI-Powered Field Content Generation with Unified Zutto AI Provider & Full Field Type Support

**Branch**: `001-ai-field-generation` | **Plan**: [plan.md](plan.md) | **Spec**: [spec.md](spec.md)  
**App**: `zutto_ai_fields`  
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

## Format: `- [ ] [ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel
- **[Story]**: Aligned User Story (`[US1]`, `[US2]`, `[US3]`)

---

## Phase 1: Setup & Scaffolding

- [x] T001 [P] Configure Python dependencies in `requirements.txt` → [`requirements.txt`](../../requirements.txt)
- [x] T002 Update `hooks.py` with app metadata, Desk assets, and permission hooks → [`zutto_ai_fields/hooks.py`](../../zutto_ai_fields/hooks.py)
- [x] T003 Update `README.md` with full fieldtype support (Text, Link, Date, Child Tables) → [`README.md`](../../README.md)

---

## Phase 2: Foundational Unified Data Layer (DocTypes)

- [x] T010 [P] [US1] Create Master DocType `Zutto AI Provider` with `Qwen (Token Plan)` and `MiMo (Token Plan)` options and 1024 length `api_key` → [`zutto_ai_provider.json`](../../zutto_ai_fields/zutto_ai_fields/doctype/zutto_ai_provider/zutto_ai_provider.json)
- [x] T011 [US1] Implement controller `zutto_ai_provider.py` with single-default validation and clean secret decryption → [`zutto_ai_provider.py`](../../zutto_ai_fields/zutto_ai_fields/doctype/zutto_ai_provider/zutto_ai_provider.py)
- [x] T012 [P] [US3] Update `AI Field Config` schema with composite autoname `format:{target_doctype}-{target_field}` and `Zutto AI Provider` link → [`ai_field_config.json`](../../zutto_ai_fields/zutto_ai_fields/doctype/ai_field_config/ai_field_config.json)
- [x] T013 Update `ai_field_config.py` validation to permit all data fieldtypes (`Link`, `Date`, `Datetime`, `Time`, `Table`, `Table MultiSelect`), restricting only layout breaks and binary attachments → [`ai_field_config.py`](../../zutto_ai_fields/zutto_ai_fields/doctype/ai_field_config/ai_field_config.py)

---

## Phase 3: Provider Strategy Layer

- [x] T020 [P] [US1] Base provider interface and `LLMResponse` → [`services/providers/base.py`](../../zutto_ai_fields/services/providers/base.py)
- [x] T021 [P] [US1] Implement `AnthropicProvider` (Claude) → [`services/providers/anthropic_provider.py`](../../zutto_ai_fields/services/providers/anthropic_provider.py)
- [x] T022 [P] [US1] Implement `OpenAIProvider` with base URL override → [`services/providers/openai_provider.py`](../../zutto_ai_fields/services/providers/openai_provider.py)
- [x] T023 [P] [US1] Implement `GeminiProvider` → [`services/providers/gemini_provider.py`](../../zutto_ai_fields/services/providers/gemini_provider.py)
- [x] T024 [P] [US1] Implement `GLMProvider` → [`services/providers/glm_provider.py`](../../zutto_ai_fields/services/providers/glm_provider.py)
- [x] T025 [P] [US1] Implement `CustomProvider` with auto whitespace/bearer stripping → [`services/providers/custom_provider.py`](../../zutto_ai_fields/services/providers/custom_provider.py)
- [x] T026 [US2] Provider resolution engine handling `Qwen (Token Plan)` and `MiMo (Token Plan)` defaults → [`services/llm_service.py`](../../zutto_ai_fields/services/llm_service.py)

---

## Phase 4: API & Security Layer

- [x] T030 [US1] Whitelisted endpoint `zutto_ai_fields.api.test_provider_connection` → [`zutto_ai_fields/api.py`](../../zutto_ai_fields/api.py)
- [x] T031 [US2] Whitelisted endpoint `zutto_ai_fields.api.generate_content` → [`zutto_ai_fields/api.py`](../../zutto_ai_fields/api.py)
- [x] T032 [P] [US3] Whitelisted endpoint `zutto_ai_fields.api.test_ai_field_config` → [`zutto_ai_fields/api.py`](../../zutto_ai_fields/api.py)
- [x] T033 [US1] Permissions scoped to `System Manager` in `permissions.py` → [`zutto_ai_fields/permissions.py`](../../zutto_ai_fields/permissions.py)

---

## Phase 5: Desk Frontend & Full Field Type Ingestion

- [x] T040 [US1] Form script `zutto_ai_provider.js` with auto-filling token plan endpoints and Test Connection button → [`public/js/zutto_ai_provider.js`](../../zutto_ai_fields/public/js/zutto_ai_provider.js)
- [x] T041 [US3] Form script `ai_field_config.js` with provider filtering → [`public/js/ai_field_config.js`](../../zutto_ai_fields/public/js/ai_field_config.js)
- [x] T042 [US1] Implement full fieldtype value setter in `public/js/ai_field_button.js`:
  - JSON array parsing & `frm.add_child()` for `Table` and `Table MultiSelect`
  - Date & Time ISO regex extraction for `Date`, `Datetime`, `Time`
  - Numeric parsing for `Int`, `Float`, `Currency`, `Percent`
  - String normalization for `Link` and `Dynamic Link`
  - Table grid header button placement

---

## Phase 6: Direct Schema Verification & Testing

- [x] T050 [US1] Verify single-default invariant on `Zutto AI Provider`.
- [x] T051 [US1] Verify 1024-character `api_key` storage without truncation.
- [x] T052 Test child table row generation and date/link assignment on `johan.localhost`.
