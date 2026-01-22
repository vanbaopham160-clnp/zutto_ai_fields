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

        // Find label and append button
        const $label = $wrapper.find('label').first();
        if ($label.length) {
            $label.append($button);
        } else {
            $wrapper.prepend($button);
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
                        // Set the generated content
                        this.frm.set_value(fieldname, result.content);

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

    // Skip AI Field Config and Zutto AI Settings
    if (frm.doctype === 'AI Field Config' || frm.doctype === 'Zutto AI Settings') return;

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
    // Patch into form refresh
    if (frappe.ui && frappe.ui.form && frappe.ui.form.Form) {
        const origRefresh = frappe.ui.form.Form.prototype.refresh;
        frappe.ui.form.Form.prototype.refresh = function(docname) {
            const result = origRefresh.apply(this, arguments);

            // Initialize AI buttons after refresh
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
