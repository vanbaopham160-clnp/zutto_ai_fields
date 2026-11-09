frappe.provide('zutto_ai_fields');

zutto_ai_fields.AIFieldButton = class AIFieldButton {
    constructor(frm) {
        this.frm = frm;
        this.configs = [];
        this.is_generating = false;
    }

    async init() {
        try {
            await frappe.call({
                method: 'zutto_ai_fields.api.get_ai_field_configs',
                args: { doctype: this.frm.doctype },
                callback: (r) => {
                    if (r.message && r.message.length > 0) {
                        this.configs = r.message;
                        this.add_buttons();
                    }
                }
            });
        } catch (error) {
            console.error('Failed to load AI field configs:', error);
        }
    }

    add_buttons() {
        if (this.configs.length === 0) return;

        // Add AI button to each target field
        this.configs.forEach(config => {
            this.add_ai_button_to_field(config.target_field, config);
        });
    }

    add_ai_button_to_field(fieldname, config) {
        const field = this.frm.get_field(fieldname);
        if (!field || !field.$wrapper) return;

        const $wrapper = field.$wrapper;

        // Check if button already exists
        if ($wrapper.find('.ai-generate-btn').length > 0) return;

        // Create button
        const $button = $(`
            <button type="button" class="ai-generate-btn btn btn-xs btn-default" style="margin-left: 10px;">
                <span class="ai-btn-icon">✨</span> AI Generate
            </button>
        `);

        // Add click handler
        $button.on('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.generate_content(fieldname, config, $button);
        });

        // Find label or grid header to append button
        const $gridHeader = $wrapper.find('.grid-heading-row .grid-header-toolbar, .form-grid label').first();
        const $label = $wrapper.find('label').first();

        if ($gridHeader.length) {
            $gridHeader.append($button);
        } else if ($label.length) {
            $label.append($button);
        } else {
            $wrapper.prepend($button);
        }
    }

    apply_generated_content(fieldname, raw_content) {
        const field = this.frm.get_field(fieldname);
        if (!field || !field.df) {
            this.frm.set_value(fieldname, raw_content);
            return;
        }

        const ftype = field.df.fieldtype;

        if (ftype === 'Table') {
            // Child Table handling
            let rows = [];
            const clean = String(raw_content).replace(/```(?:json)?/gi, '').replace(/```/g, '').trim();
            try {
                const parsed = JSON.parse(clean);
                rows = Array.isArray(parsed) ? parsed : [parsed];
            } catch (e) {
                // If not valid JSON, treat each non-empty line as a row
                const lines = clean.split('\n').map(l => l.replace(/^[-*•\d.]+\s*/, '').trim()).filter(Boolean);
                const child_meta = frappe.get_meta(field.df.options);
                const primary_field = child_meta ? child_meta.fields.find(f => ['Data', 'Text', 'Small Text'].includes(f.fieldtype)) : null;
                const target_col = primary_field ? primary_field.fieldname : 'description';
                rows = lines.map(line => ({ [target_col]: line }));
            }

            if (rows.length > 0) {
                rows.forEach(row_data => {
                    if (typeof row_data === 'object' && row_data !== null) {
                        this.frm.add_child(fieldname, row_data);
                    }
                });
                this.frm.refresh_field(fieldname);
            }
        } else if (ftype === 'Table MultiSelect') {
            // Table MultiSelect handling
            let items = [];
            const clean = String(raw_content).replace(/```(?:json)?/gi, '').replace(/```/g, '').trim();
            try {
                const parsed = JSON.parse(clean);
                items = Array.isArray(parsed) ? parsed : [parsed];
            } catch (e) {
                items = clean.split(/[\n,]+/).map(s => s.replace(/^[-*•\d.]+\s*/, '').trim()).filter(Boolean);
            }

            const child_meta = frappe.get_meta(field.df.options);
            const link_field = child_meta ? child_meta.fields.find(f => f.fieldtype === 'Link') : null;
            const target_col = link_field ? link_field.fieldname : 'item';

            items.forEach(item => {
                const val = typeof item === 'object' ? (item[target_col] || Object.values(item)[0]) : item;
                if (val) {
                    this.frm.add_child(fieldname, { [target_col]: String(val).trim() });
                }
            });
            this.frm.refresh_field(fieldname);
        } else if (ftype === 'Date') {
            const match = String(raw_content).match(/\b\d{4}-\d{2}-\d{2}\b/);
            this.frm.set_value(fieldname, match ? match[0] : String(raw_content).trim());
        } else if (ftype === 'Datetime') {
            const match = String(raw_content).match(/\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?\b/);
            this.frm.set_value(fieldname, match ? match[0].replace('T', ' ') : String(raw_content).trim());
        } else if (ftype === 'Time') {
            const match = String(raw_content).match(/\b\d{2}:\d{2}(?::\d{2})?\b/);
            this.frm.set_value(fieldname, match ? match[0] : String(raw_content).trim());
        } else if (['Int', 'Float', 'Currency', 'Percent'].includes(ftype)) {
            const clean_num = String(raw_content).replace(/[^0-9.-]/g, '');
            const num = ftype === 'Int' ? parseInt(clean_num, 10) : parseFloat(clean_num);
            this.frm.set_value(fieldname, isNaN(num) ? 0 : num);
        } else if (ftype === 'Check') {
            const str = String(raw_content).toLowerCase().trim();
            const checked = ['1', 'true', 'yes', 'y', 'checked'].includes(str) ? 1 : 0;
            this.frm.set_value(fieldname, checked);
        } else if (['Link', 'Dynamic Link', 'Select'].includes(ftype)) {
            const clean_val = String(raw_content).trim().replace(/^["'`]|["'`]$/g, '').trim();
            this.frm.set_value(fieldname, clean_val);
        } else {
            // Standard Text, Data, Text Editor, Code, etc.
            this.frm.set_value(fieldname, raw_content);
        }
    }

    async generate_content(fieldname, config, $button) {
        if (this.is_generating) {
            frappe.show_alert({ message: 'Already generating...', indicator: 'orange' });
            return;
        }

        // Get current document values
        const doc = this.frm.doc;

        // Show loading state
        this.is_generating = true;
        const originalHtml = $button.html();
        $button.html('<span class="spinner-grow spinner-grow-sm"></span> Generating...').prop('disabled', true);

        try {
            await frappe.call({
                method: 'zutto_ai_fields.api.generate_content',
                args: {
                    config_name: config.name,
                    doc: doc
                },
                callback: (r) => {
                    const result = r.message;

                    if (result && result.success) {
                        // Apply the generated content according to fieldtype
                        this.apply_generated_content(fieldname, result.content);

                        frappe.show_alert({
                            message: `Generated using ${result.provider} (${result.model})`,
                            indicator: 'green'
                        }, 5);
                    } else {
                        const errorMessages = {
                            'invalid_key': 'API key not configured or invalid.',
                            'rate_limit': 'Rate limit exceeded. Try again later.',
                            'timeout': 'Request timed out. Try again.',
                            'api_error': 'API error occurred.',
                            'disabled': 'AI generation is disabled.',
                            'permission': 'No permission to use AI generation.',
                            'not_found': 'AI Field Config not found.',
                            'unknown': 'An unexpected error occurred.'
                        };

                        const error_msg = (result && errorMessages[result.error_type]) ||
                                         (result && result.error) ||
                                         'Unknown error';

                        frappe.show_alert({
                            message: error_msg,
                            indicator: 'red'
                        }, 8);
                    }
                }
            });
        } catch (error) {
            frappe.show_alert({
                message: 'Failed to connect to AI service.',
                indicator: 'red'
            }, 8);
            console.error('Generation error:', error);
        } finally {
            this.is_generating = false;
            $button.html(originalHtml).prop('disabled', false);
        }
    }
};

// Track which forms have been initialized
zutto_ai_fields.initialized_forms = {};

// Function to initialize AI buttons for a form
zutto_ai_fields.init_for_form = function(frm) {
    if (!frm || !frm.doctype) return;

    // Skip AI Field Config and Zutto AI Provider
    if (frm.doctype === 'AI Field Config' || frm.doctype === 'Zutto AI Provider' || frm.doctype === 'Zutto AI Settings') return;

    // Create unique key for this form instance
    const form_key = frm.doctype + '-' + (frm.docname || 'new');

    // Check if already initialized
    if (zutto_ai_fields.initialized_forms[form_key]) return;

    // Mark as initialized
    zutto_ai_fields.initialized_forms[form_key] = true;

    // Initialize AI buttons
    const aiButton = new zutto_ai_fields.AIFieldButton(frm);
    aiButton.init();
};

// Method 1: Override frappe.ui.form.Form refresh
$(document).ready(function() {
    if (frappe.ui && frappe.ui.form && frappe.ui.form.Form) {
        const origRefresh = frappe.ui.form.Form.prototype.refresh;
        frappe.ui.form.Form.prototype.refresh = function(docname) {
            const result = origRefresh.apply(this, arguments);

            setTimeout(() => {
                if (this.frm) {
                    zutto_ai_fields.init_for_form(this.frm);
                } else if (cur_frm) {
                    zutto_ai_fields.init_for_form(cur_frm);
                }
            }, 500);

            return result;
        };
    }
});

// Method 2: Listen for page changes
$(document).on('page-change', function() {
    setTimeout(() => {
        if (cur_frm) {
            zutto_ai_fields.init_for_form(cur_frm);
        }
    }, 1000);
});

// Method 3: Periodic check (fallback)
setInterval(() => {
    if (cur_frm && cur_frm.doc && cur_frm.doctype) {
        zutto_ai_fields.init_for_form(cur_frm);
    }
}, 2000);
