# Zutto AI Fields

AI-powered field content generation for Frappe. Allows System Managers to configure which fields display an AI generation button, define prompts with field placeholders, and generate content using various LLM providers.

## Features

- **AI Button Injection**: Automatic AI generation buttons next to configured fields
- **Multiple LLM Providers**: Support for OpenAI and Google Gemini
- **Prompt Templates**: Use `{{field_name}}` placeholders for dynamic content generation
- **Field-level Configuration**: Configure AI generation per DocType and field
- **Secure**: API keys stored encrypted, all API calls server-side
- **Permission-aware**: Only shows buttons to users with write access

## Installation

### Prerequisites

- Frappe 14+ installed
- Python 3.8+
- Redis server running

### Step 1: Install Dependencies

Install the required Python packages:

```bash
cd /path/to/frappe-bench/apps/zutto_ai_fields
pip install -r requirements.txt
```

### Step 2: Install the App

Install the app in your Frappe bench:

```bash
cd /path/to/frappe-bench
bench get-app zutto_ai_fields
```

Or if you already have the app folder:

```bash
cd /path/to/frappe-bench
bench install-app zutto_ai_fields
```

### Step 3: Install in Your Site

Install the app in your specific Frappe site:

```bash
bench --site your-site.name install-app zutto_ai_fields
```

### Step 4: Migrate and Build

Run migrations and build assets:

```bash
bench --site your-site.name migrate
bench build
```

## Configuration

### Step 1: Configure Global Settings

1. Log in as **System Manager**
2. Go to **Zutto AI Settings** from the Awesome Bar
3. Configure the following:

   **Basic Settings:**
   - ✅ Enable AI Field Generation
   - Default Provider: Select (OpenAI or Gemini)
   - Default Model: Enter model name (e.g., `gpt-4o-mini` for OpenAI)

   **Provider API Keys:**
   - **OpenAI**: Enter your API key (starts with `sk-`)
   - **Gemini**: Enter your API key (starts with `AIza`)

   **Advanced Settings:**
   - Max Tokens: 1000 (default)
   - Request Timeout: 30 seconds (default)
   - Rate Limit: 60 requests per minute (default)

4. Click **Test Connection** to verify your API key is working
5. Click **Save**

### Step 2: Create AI Field Configurations

1. Go to **AI Field Config** from the Awesome Bar
2. Click **+ Add AI Field Config**
3. Configure the following:

   **Basic Info:**
   - ✅ Enabled
   - Target DocType: Select the DocType (e.g., `User`)
   - Target Field: Select the field to generate content for (e.g., `bio`)

   **Prompt Configuration:**
   - Prompt Template: Enter your prompt with placeholders
     - Example: `Write a short professional bio for {{email}}`
   - System Prompt: (Optional) Add system instructions
     - Example: `You are a bio writer. Write only a short 1-2 sentence professional bio. No headers, no formatting.`

   **Provider Override:**
   - ✅ Override Provider: Check if you want to use a different provider for this field
   - Provider: Select provider (if overriding)
   - Model: Enter model name (if overriding)

4. Click **Save**
5. Click **Test Generation** to verify the configuration works

## Usage Example: User Doctype

### Scenario: Auto-generate User Bio

Let's configure AI generation for the User bio field.

#### Step 1: Configure Global Settings

1. Go to **Zutto AI Settings**
2. Enable AI Field Generation
3. Set Default Provider to **OpenAI**
4. Set Default Model to **gpt-4o-mini**
5. Enter your OpenAI API key
6. Click **Test Connection** (should show "Connection successful")
7. Click **Save**

#### Step 2: Create AI Field Config for User Bio

1. Go to **AI Field Config**
2. Click **+ Add AI Field Config**
3. Fill in the form:

   ```
   Enabled: ✅
   Target DocType: User
   Target Field: bio

   Prompt Template: Write a short professional bio for {{email}}

   System Prompt: You are a bio writer. Write only a short 1-2 sentence
   professional bio. No headers, no sections, no formatting. Just plain text.
   ```

4. Click **Save**
5. Click **Test Generation** to see a sample output

#### Step 3: Using the AI Button

1. Go to **User List**
2. Open an existing User or create a new one
3. In the User form, you'll see an **✨ AI Generate** button next to the Bio field
4. Click **✨ AI Generate**
5. Wait for the generation (loading spinner)
6. The bio will be automatically populated
7. Review and edit as needed

#### Example Output

If you have a User with:
- Email: "john.doe@example.com"

The AI might generate:
```
John is a dedicated professional with expertise in technology and business operations, committed to delivering innovative solutions and driving organizational success.
```

### Advanced Example: Multiple Fields

You can configure AI generation for multiple fields in the same DocType:

#### 1. User Bio
```
Prompt: Write a short professional bio for {{email}}
System Prompt: Write only 1-2 sentences. No formatting.
```

#### 2. User Interest
```
Prompt: Suggest professional interests for a user with email {{email}}
System Prompt: List 3-5 professional interests, comma-separated.
```

## Supported Field Types

### ✅ Supported
- **Data**: Short text fields
- **Text**: Single-line text
- **Small Text**: Multi-line text
- **Long Text**: Extended text fields
- **Text Editor**: Rich text editor
- **Code**: Code editor
- **Markdown Editor**: Markdown editor
- **HTML Editor**: HTML editor
- **Select**: Dropdown (generates from allowed options)
- **Int**: Integer numbers
- **Float**: Decimal numbers
- **Currency**: Monetary values
- **Percent**: Percentage values

### ❌ Not Supported
- Link (use standard link field)
- Dynamic Link
- Table (child tables)
- Table MultiSelect
- Layout fields (Section Break, Column Break, Tab Break)
- Attachments
- Dates and Times

## API Reference

### Backend API Methods

#### `get_ai_field_configs(doctype)`
Get all enabled AI field configurations for a DocType.

**Parameters:**
- `doctype` (string): The DocType name

**Returns:**
- List of configs with `name`, `target_field`, `prompt_template`, `system_prompt`

**Example:**
```python
configs = frappe.call('zutto_ai_fields.api.get_ai_field_configs', doctype='User')
```

#### `generate_content(config_name, doc)`
Generate AI content for a specific field configuration.

**Parameters:**
- `config_name` (string): AI Field Config name
- `doc` (dict): Current document values

**Returns:**
```python
{
    "success": True,
    "content": "Generated content here...",
    "provider": "openai",
    "model": "gpt-4o-mini"
}
# OR
{
    "success": False,
    "error": "Error message",
    "error_type": "api_error|rate_limit|timeout|invalid_key"
}
```

**Example:**
```python
doc = frappe.get_doc('User', 'john@example.com')
response = frappe.call(
    'zutto_ai_fields.api.generate_content',
    config_name='User',
    doc=doc
)
```

#### `test_connection(provider)`
Test connection to a specific LLM provider.

**Parameters:**
- `provider` (string): Provider name (openai, gemini)

**Returns:**
```python
{
    "success": True,
    "message": "Connection successful! Response: Hello, World!..."
}
# OR
{
    "success": False,
    "error": "Error message"
}
```

## Error Handling

### Common Errors and Solutions

| Error Type | Cause | Solution |
|------------|-------|----------|
| **Invalid API Key** | API key not configured or incorrect | Check Zutto AI Settings and verify your API key |
| **Rate Limit** | Too many requests | Wait a few minutes and try again |
| **Timeout** | Request took too long | Increase timeout in settings or try again |
| **Connection Error** | Network issue | Check internet connection |
| **Disabled** | AI generation is disabled | Enable in Zutto AI Settings |
| **Permission** | User lacks permissions | Contact System Manager |

### Error Messages

The app provides user-friendly error messages:
- "API key not configured or invalid. Please check settings."
- "Rate limit exceeded. Please try again later."
- "Request timed out. Please try again."
- "AI generation is disabled in settings."
- "You do not have permission to use AI generation."

## Security

### API Key Storage
- API keys are stored as **encrypted Password fields** in Zutto AI Settings
- Never exposed to the client-side
- Only accessible by System Managers

### Server-Side Processing
- All LLM API calls are made server-side
- Document data is sent securely to the LLM provider
- No sensitive data is logged

### Permissions
- **Zutto AI Settings**: Only System Managers can access
- **AI Field Config**: System Managers can create/edit, AI Field Users can read
- **AI Generation**: Requires write permission on the target DocType

## Troubleshooting

### AI Button Not Appearing

1. **Check if app is installed:**
   ```bash
   bench --site your-site.name list-apps
   ```

2. **Verify AI Field Config:**
   - Go to AI Field Config
   - Ensure config is enabled
   - Verify Target DocType and Field are correct

3. **Check permissions:**
   - User must have write permission on the DocType
   - Document must be saved (not new)

4. **Clear cache:**
   ```bash
   bench --site your-site.name clear-cache
   bench build
   ```

### Generation Fails

1. **Test connection:**
   - Go to Zutto AI Settings
   - Click Test Connection
   - Verify API key is valid

2. **Check logs:**
   ```bash
   bench --site your-site.name logs
   ```

3. **Verify prompt template:**
   - Ensure placeholders match document fields
   - Test with Test Generation button

### Performance Issues

1. **Increase timeout:**
   - Go to Zutto AI Settings
   - Increase Request Timeout (default: 30s)

2. **Check rate limits:**
   - Review your LLM provider's rate limits
   - Consider upgrading plan if needed

3. **Use caching:**
   - AI Field Configs are cached for 5 minutes
   - Clear cache if configs change frequently

## Development

### Adding New LLM Providers

1. Create a new provider class in `services/providers/`:
   ```python
   # services/providers/custom_provider.py
   from .base import BaseLLMProvider, LLMResponse

   class CustomProvider(BaseLLMProvider):
       def generate(self, prompt, system_prompt="", max_tokens=1000, timeout=30):
           # Implement your provider logic
           pass
   ```

2. Update `services/providers/__init__.py`:
   ```python
   from .custom_provider import CustomProvider
   ```

3. Update `services/llm_service.py`:
   ```python
   elif provider == "custom":
       llm_provider = CustomProvider(api_key=api_key, **config)
   ```

4. Update `zutto_ai_settings/zutto_ai_settings.json`:
   - Add provider to default_provider options

### Customizing Frontend

1. Edit `public/js/ai_field_button.js` to change button behavior
2. Edit `public/css/ai_field.css` to change button styling
3. Rebuild assets: `bench build`

### Extending DocTypes

1. Add custom fields to AI Field Config:
   ```python
   # hooks.py
   doctype_list_js = {
       "AI Field Config": "public/js/custom_ai_field_config.js"
   }
   ```

2. Add custom validation in `ai_field_config/ai_field_config.py`

## Requirements

- Frappe 14+
- Python 3.8+
- Redis server
- Dependencies:
  - `openai>=1.0.0`
  - `google-generativeai>=0.3.0`
  - `requests>=2.28.0`

## License

MIT

## Support

For issues and questions:
- Check the logs: `bench --site your-site.name logs`
- Review error messages in the UI
- Verify configuration in Zutto AI Settings