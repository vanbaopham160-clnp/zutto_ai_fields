# Feature Specification: AI-Powered Field Content Generation with Unified Zutto AI Provider & Full Field Type Support

**Feature Branch**: `001-ai-field-generation`  
**Created**: 2026-11-09  
**Status**: Revised (Comprehensive Field Support: Scalar, Link, Date/Time, & Child Tables)  
**App**: `zutto_ai_fields`  
**Input**: Comprehensive field-level generative AI assistance within Frappe Desk forms supporting all data-bearing field types: Text, Numbers, Select, Link, Dynamic Link, Dates, Times, Table MultiSelect, and Child Tables (`Table`). Only structural layout dividers (`Section Break`, `Column Break`, `Tab Break`, `Fold`) and binary file uploads (`Attach`, `Attach Image`, `Signature`) are excluded. Powered by the unified `Zutto AI Provider` registry (Claude, OpenAI, Gemini, GLM, Qwen Token Plan, MiMo Token Plan, and Custom).

---

## 1. Architecture Context

Frappe Framework provides standard Desk Form rendering for all System and Custom DocTypes. `zutto_ai_fields` injects generative AI capabilities across all data fields:

1. **`Zutto AI Provider` (Master DocType)**: Unified repository for all AI provider credentials, models, endpoints, and runtime parameters.
2. **`AI Field Config` (Master DocType)**: Maps `(target_doctype, target_field)` to custom prompt templates and field-specific behavior.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Frappe Desk UI                                            │
│                                                                                             │
│  Desk Form View [e.g. Quotation / Task / Item / User]                                       │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ Scalar / Link / Date: Description [ ✨ AI Generate ]  -> frm.set_value()               │ │
│  │ Child Table: Items [ ✨ AI Generate ]                 -> frm.add_child() & refresh     │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────▲───────────────────────────────────────┬─────────────────────────┘
                            │                                       │
              1. get_ai_field_configs()                             │ 2. generate_content()
              (on form load)                                        │ (doc values + config)
                            │                                       │
┌───────────────────────────┴───────────────────────────────────────▼─────────────────────────┐
│                                 Frappe Backend                                              │
│                                                                                             │
│                                                       ┌─────────────────────────────────┐   │
│                                                       │    Prompt Service               │   │
│                                                       │  (Template & {{field}} sub)     │   │
│                                                       └────────────────┬────────────────┘   │
│                                                                        │                    │
│                                                                        ▼                    │
│                                   ┌─────────────────────────────────────────────────────┐   │
│                                   │                  Resolution Engine                  │   │
│                                   │  1. Check Field Config: provider override?          │   │
│                                   │  2. If not, resolve Zutto AI Provider where         │   │
│                                   │     default_provider=1 and active=1                 │   │
│                                   │  3. Retrieve encrypted API key, model & base URL    │   │
│                                   └──────────────────────────┬──────────────────────────┘   │
│                                                              │                              │
│   ┌──────────────────────────────────────────────────────────┴──────────────────────────┐   │
│   │                      Zutto AI Provider Registry (Single DocType Model)              │   │
│   │  Claude | ChatGPT | Gemini | GLM | Qwen (Token Plan) | MiMo (Token Plan) | Custom   │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Comprehensive Field Type Support Matrix

Except for pure visual dividers and binary media attachments, **all data-bearing Frappe field types are supported**:

| Category | Supported Field Types | AI Output Format & Population Mechanism |
|:---|:---|:---|
| **Text & Prose** | `Data`, `Text`, `Small Text`, `Long Text`, `Text Editor`, `Code`, `Markdown Editor`, `HTML Editor` | Direct string assignment via `frm.set_value(fieldname, content)`. |
| **Numeric** | `Int`, `Float`, `Currency`, `Percent` | Extracts numeric value (stripping currency symbols/units), parses float/int, and sets via `frm.set_value(fieldname, num)`. |
| **Selection** | `Select`, `Check` | Matches string against allowed options or boolean (1/0). |
| **Reference / Links** | `Link`, `Dynamic Link` | Extracts target document name/identifier and sets via `frm.set_value(fieldname, doc_name)`. |
| **Temporal** | `Date`, `Datetime`, `Time` | Formats and normalizes ISO strings (`YYYY-MM-DD`, `YYYY-MM-DD HH:mm:ss`, `HH:mm:ss`) and sets via `frm.set_value()`. |
| **Child Tables** | `Table` | Parses structured JSON array (`[{"col1": "...", "col2": ...}]`) or newline rows, appends each row via `frm.add_child(fieldname, row_data)`, and triggers `frm.refresh_field(fieldname)`. |
| **Multi-Select Tables** | `Table MultiSelect` | Parses JSON array of strings or comma-separated tokens, populates child link rows via `frm.add_child()`, and refreshes field. |

### ❌ Genuinely Unsupported (Exempt by Nature):
- **Layout & Structure Fields**: `Section Break`, `Column Break`, `Tab Break`, `Fold` (contain no database column, data, or user input).
- **Binary File Uploads**: `Attach`, `Attach Image`, `Signature` (require binary media file streams rather than LLM text generation).
- **Static Display Elements**: `Heading`, `HTML` (read-only static UI containers).

---

## 3. User Scenarios & Acceptance Criteria *(Mandatory)*

### User Story 1 — Populate Child Table Rows from AI (Priority: P1)

As a Desk user editing a document with child tables (e.g. `Quotation.items` or `Project.tasks`), I want to click "✨ AI Generate" on the child table to automatically generate and append multiple structured rows.

**Acceptance Scenarios**:
1. **Given** an `AI Field Config` for a `Table` field with a prompt requesting JSON output, **When** the user clicks "✨ AI Generate", **Then** the LLM generates a JSON array of row objects.
2. **Given** valid JSON array returned, **When** processed by the Desk form, **Then** existing empty rows are cleared, each item is appended via `frm.add_child()`, and `frm.refresh_field()` renders the populated grid.
3. **Given** Markdown code fences surrounding the JSON (e.g. ```` ```json [...] ``` ````), **When** received, **Then** the client strips code fences and parses the JSON array cleanly.

---

### User Story 2 — Populate Date, Time, and Link Reference Fields (Priority: P1)

As a Desk user, I want AI generation to populate Link fields (e.g. `Item.item_group`) and Date fields (e.g. `Task.exp_end_date`) by resolving appropriate values from the document context.

**Acceptance Scenarios**:
1. **Given** an `AI Field Config` for a `Date` field, **When** the AI returns a date string, **Then** the date is normalized to `YYYY-MM-DD` and saved via `frm.set_value()`.
2. **Given** an `AI Field Config` for a `Link` field, **When** the AI generates the document identifier, **Then** `frm.set_value()` assigns the link key without formatting errors.

---

### User Story 3 — Manage Multiple AI Providers in Zutto AI Provider (Priority: P1)

As a System Manager, I want to create and manage multiple AI provider records (`Claude`, `ChatGPT`, `Gemini`, `GLM`, `Qwen (Token Plan)`, `MiMo (Token Plan)`) with separate keys, default models, and base URLs.

**Acceptance Scenarios**:
1. **Given** a `Zutto AI Provider` saved with `default_provider = 1`, **When** saved, **Then** all other records have `default_provider` set to `0`.
2. **Given** `Qwen (Token Plan)` or `MiMo (Token Plan)` selected, **When** chosen, **Then** dedicated token-plan base URLs and models are auto-suggested.

---

## 4. Functional Requirements

- **FR-001**: System shall support AI button injection and generation for all data fieldtypes: `Data`, `Text`, `Small Text`, `Long Text`, `Text Editor`, `Code`, `Markdown Editor`, `HTML Editor`, `Select`, `Check`, `Int`, `Float`, `Currency`, `Percent`, `Date`, `Datetime`, `Time`, `Link`, `Dynamic Link`, `Table`, and `Table MultiSelect`.
- **FR-002**: System must explicitly reject configuration only for structural layout fields (`Section Break`, `Column Break`, `Tab Break`, `Fold`) and binary uploads (`Attach`, `Attach Image`, `Signature`).
- **FR-003**: For `Table` child fields, client script `ai_field_button.js` must detect JSON array format (`[...]`), iterate items, invoke `frm.add_child(fieldname, item)`, and refresh the grid.
- **FR-004**: For `Table MultiSelect` fields, client script must map array of strings into child table rows matching the child link fieldname.
- **FR-005**: For `Date`, `Datetime`, and `Time` fields, client script must sanitize and format extracted values matching Frappe's expected temporal format.
- **FR-006**: For numeric fields (`Int`, `Float`, `Currency`, `Percent`), client script must strip currency symbols and cast strings to numeric types before `frm.set_value()`.
- **FR-007**: System shall provide `Zutto AI Provider` as a standard Master DocType under module `AI` with providers: `Anthropic (Claude)`, `OpenAI (ChatGPT)`, `Google Gemini`, `GLM (Zhipu AI)`, `Qwen (Token Plan)`, `MiMo (Token Plan)`, `Custom / Ollama`.
- **FR-008**: System must enforce single-default integrity: saving an active provider with `default_provider = 1` must set `default_provider = 0` on all other records.
- **FR-009**: System must provide a "Test Connection" button on the `Zutto AI Provider` form that verifies API connectivity with a prompt and displays the response snippet.
- **FR-010**: `api_key` in `Zutto AI Provider` must have length `1024` (stored as `TEXT` in MariaDB) to prevent truncation of long tokens.

---

## 5. Security & Non-Functional Requirements

- **NFR-001 (Zero Secret Leakage)**: API keys in `Zutto AI Provider` must be `Password` fieldtype and never serialized in client responses or logs.
- **NFR-002 (Role Scoping)**: Only `System Manager` may create, edit, or test `Zutto AI Provider` records.
- **NFR-003 (Custom Proxy Support)**: All providers must respect `base_url_override` for proxies and private deployments.

### User Story 4 — Many-to-One & Many-to-Many Prompt Placeholders (Priority: P1)

As a prompt author, I want to reference Many-to-One (Link) and Many-to-Many (Table, Table MultiSelect) fields in prompt templates so the LLM receives complete relational context.

Acceptance Scenarios:
1. Given a Many-to-One Link field (e.g. customer), When prompt is rendered, Then the foreign document key/ID is injected directly.
2. Given a Many-to-Many Table or Table MultiSelect field (e.g. roles, user_group_members), When prompt is rendered, Then the list of row dictionaries is cleanly serialized as standard JSON.
3. Given a prompt with {{doc.fieldname}} or {{fieldname}}, When evaluated, Then doc. prefix is normalized and missing fields are handled gracefully without runtime exceptions.

---

## 6. Test Suite & Verification Matrix

The codebase includes an automated unit test suite executed via bench run-tests --app zutto_ai_fields:
- TestZuttoAIProvider (5 tests):
  - Default values, active flag enforcement.
  - Single-default invariant (updating one active default unsets all others).
  - API key Bearer prefix and whitespace stripping.
  - 1024-character password field storage (TEXT storage without truncation).
- TestAIFieldConfig (5 tests):
  - Composite autoname format:{target_doctype}-{target_field}.
  - Comprehensive field type permissibility test across 15 standard field types (Data, Small Text, Text Editor, Select, Check, Date, Datetime, Time, Int, Float, Currency, Link, Dynamic Link, Table, Table MultiSelect, Code).
  - Prohibited field type rejection test (Section Break, Column Break, Tab Break, Attach Image).
  - Non-existent field validation.
  - Placeholder help HTML and preview rendering.
- TestServicesAndAPI (8 tests):
  - build_prompt, extract_placeholders, validate_placeholders.
  - Default endpoints for Qwen (Token Plan) and MiMo (Token Plan).
  - Custom / Ollama Bearer and URL normalization.
  - Provider resolution precedence (override vs default).
  - API RPC tests (get_ai_field_configs, generate_content, test_provider_connection).
