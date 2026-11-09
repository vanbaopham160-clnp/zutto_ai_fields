# Implementation Plan: AI-Powered Field Content Generation with Full Field Type Support

**Branch**: `001-ai-field-generation` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)  
**App**: `zutto_ai_fields`  
**Input**: Comprehensive field-level generative AI assistance across Frappe forms supporting all data-bearing field types (Text, Number, Link, Date/Time, Child Tables, Table MultiSelect).

---

## 1. System Architecture & Flow

```mermaid
flowchart TD
    subgraph Client["Client Browser (Frappe Desk Form)"]
        User["User Form Interaction"]
        Button["✨ AI Generate Button (ai_field_button.js)"]
        Handler["Field Type Value Setter<br/>(Scalar, Link, Date, Child Table)"]
        Grid["Child Table Grid (frm.add_child)"]
        FieldControl["Field Control (frm.set_value)"]
    end

    subgraph Backend["Frappe Backend"]
        API["generate_content (api.py)"]
        Resolver["resolve_provider_and_model (llm_service.py)"]
        PromptEngine["build_prompt (prompt_service.py)"]
        ProviderDoc["Zutto AI Provider"]
        FieldConfig["AI Field Config"]
        ProviderStrategy["BaseLLMProvider Strategy Factory"]
    end

    User -->|Click ✨ AI Generate| Button
    Button -->|Call generate_content| API
    API -->|Resolve provider| Resolver
    Resolver --> ProviderDoc
    API -->|Interpolate {{fields}}| PromptEngine
    API -->|Execute generation| ProviderStrategy
    
    API -->|Return content string or JSON| Button
    Button --> Handler
    Handler -->|If Table / Table MultiSelect| Grid
    Handler -->|If Scalar / Link / Date / Select| FieldControl
```

---

## 2. Field Type Handling & Ingestion Logic (`ai_field_button.js`)

When the LLM response is returned to Desk, `ai_field_button.js` inspects the target field's `fieldtype` and applies specialized formatting:

### 2.1 Child Tables (`Table`)
- **JSON Parsing & Fence Stripping**:
  The response string is checked for Markdown code fences (e.g. ```` ```json ... ``` ```` or ```` ``` ... ``` ````). Strips fences and parses JSON.
- **Grid Population**:
  ```javascript
  if (field.df.fieldtype === 'Table') {
      let rows = [];
      try {
          const cleaned = raw_content.replace(/```(?:json)?/gi, '').replace(/```/g, '').trim();
          rows = JSON.parse(cleaned);
      } catch (e) {
          // If not valid JSON, treat each non-empty line as a row (if child table has 1 primary field)
          rows = raw_content.split('\n').filter(l => l.trim().length > 0).map(l => ({ description: l.trim().replace(/^[-*•\d.]+\s*/, '') }));
      }

      if (Array.isArray(rows)) {
          // Ask user or append rows
          rows.forEach(row_data => {
              if (typeof row_data === 'object') {
                  this.frm.add_child(fieldname, row_data);
              }
          });
          this.frm.refresh_field(fieldname);
      }
  }
  ```

### 2.2 Table MultiSelect (`Table MultiSelect`)
- Parses JSON array of strings or comma/newline-separated strings.
- Determines the child DocType's link fieldname, appends each item using `this.frm.add_child(fieldname, { [link_fieldname]: item })`, and refreshes the field.

### 2.3 Dates, Times, and Datetimes
- **`Date`**: Normalizes regex `(\d{4}-\d{2}-\d{2})` and assigns `YYYY-MM-DD`.
- **`Datetime`**: Normalizes `YYYY-MM-DD HH:mm:ss`.
- **`Time`**: Normalizes `HH:mm:ss`.

### 2.4 Reference Fields (`Link`, `Dynamic Link`)
- Strips quotation marks, bullets, and whitespace from the returned string and assigns via `this.frm.set_value(fieldname, clean_value)`.

### 2.5 Numeric Fields (`Int`, `Float`, `Currency`, `Percent`)
- Strips currency symbols (`$`, `€`, `£`, `¥`, `,`), parses as `parseFloat` or `parseInt`, and sets numeric value.

### 2.6 Text & Editors (`Data`, `Text`, `Small Text`, `Text Editor`, `Code`, etc.)
- Direct string assignment via `this.frm.set_value(fieldname, content)`.

---

## 3. Disallowed Field Types (Exempt by Nature)

`AI Field Config` validation restricts only:
1. **Layout / Break fields**: `Section Break`, `Column Break`, `Tab Break`, `Fold`
2. **Binary Media / Attachments**: `Attach`, `Attach Image`, `Signature`
3. **Static UI Containers**: `Heading`, `HTML`

All other standard and custom Frappe field types are fully valid.

---

## 4. DocType Specifications

### 4.1 `Zutto AI Provider` (Master DocType)
- `provider_name`: Data (Unique)
- `provider`: Select (`Anthropic (Claude)`, `OpenAI (ChatGPT)`, `Google Gemini`, `GLM (Zhipu AI)`, `Qwen (Token Plan)`, `MiMo (Token Plan)`, `Custom / Ollama`)
- `api_key`: Password (Length: 1024, stored as `TEXT`)
- `base_url_override`: Data (Length: 512)
- `default_chat_model`: Data (Reqd)
- `default_embedding_model`: Data
- `default_transcription_model`: Data
- `default_provider`: Check
- `active`: Check
- `max_tokens`: Int (default: 1000)
- `request_timeout`: Int (default: 30)

### 4.2 `AI Field Config` (Master DocType)
- `target_doctype`: Link to `DocType`
- `target_field`: Data (Fieldname)
- `prompt_template`: Code
- `system_prompt`: Code
- `override_provider`: Check
- `provider`: Link to `Zutto AI Provider`
- `model`: Data
- Autoname: `format:{target_doctype}-{target_field}`

---

## 5. Implementation & Verification Plan

1. **Validation Update (`ai_field_config.py`)**:
   - Update field validation to allow `Link`, `Date`, `Datetime`, `Time`, `Table`, `Table MultiSelect`, etc.
   - Restrict only layout and attachment fields.
2. **Frontend Handler (`ai_field_button.js`)**:
   - Add `set_generated_value(fieldname, content)` implementing the fieldtype-specific logic.
   - Attach button to child table grid headers (`.grid-heading-row` or table label).
3. **Desk Testing**:
   - Test scalar fields, Link fields, Date fields, and Child Table JSON generation.


---

## 6. Prompt Service & Placeholder Resolution Architecture

- **Scalar & Relational Fields**: Standard values are extracted from `frm.doc` and cast to string.
- **Many-to-One (`Link`, `Dynamic Link`)**: Injects foreign document identifier (e.g. `CUST-0001`). Linked attributes accessed via standard DocType Fetch From fields.
- **Many-to-Many (`Table`, `Table MultiSelect`)**: Collections are serialized as valid JSON arrays (`json.dumps(value, default=str)`) so LLMs can cleanly parse and reason across child rows.
- **Syntax Compatibility**: Supports both `{{field_name}}` and `{{doc.field_name}}` formats, with order-preserving placeholder extraction.

---

## 7. Automated Test Architecture

Unit tests run natively via Frappe Test Runner (`bench run-tests --app zutto_ai_fields`):
- `zutto_ai_fields/zutto_ai_fields/doctype/zutto_ai_provider/test_zutto_ai_provider.py`: Invariants, key encryption, Bearer cleaning, 1024-char keys.
- `zutto_ai_fields/zutto_ai_fields/doctype/ai_field_config/test_ai_field_config.py`: Autoname, 15 allowed field types, 4 disallowed layout/attachment types.
- `zutto_ai_fields/tests/test_services.py`: Prompt builder, Token Plan auto-endpoints, Custom Provider headers/URLs, Provider resolution precedence, RPC endpoints.
