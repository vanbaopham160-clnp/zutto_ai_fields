frappe.ui.form.on('Zutto AI Provider', {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Test Connection'), function() {
                frm.call({
                    method: 'zutto_ai_fields.api.test_provider_connection',
                    args: {
                        provider_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Testing connection to {0}...', [frm.doc.name]),
                    callback: function(r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint({
                                title: __('Connection Successful'),
                                indicator: 'green',
                                message: r.message.message
                            });
                        } else {
                            frappe.msgprint({
                                title: __('Connection Failed'),
                                indicator: 'red',
                                message: r.message ? r.message.error : __('Unknown error occurred.')
                            });
                        }
                    }
                });
            }).addClass('btn-primary');
        }
    },

    provider: function(frm) {
        const p = (frm.doc.provider || '').toLowerCase();
        if (p.includes('anthropic') || p.includes('claude')) {
            frm.set_value('default_chat_model', 'claude-sonnet-5-5');
        } else if (p.includes('qwen')) {
            frm.set_value('default_chat_model', 'qwen3.7-max');
            if (!frm.doc.base_url_override) {
                frm.set_value('base_url_override', 'https://token-plan.maas.qwencloudapi.com/compatible-mode/v1');
            }
        } else if (p.includes('mimo')) {
            frm.set_value('default_chat_model', 'mimo-v2.5-pro');
            if (!frm.doc.base_url_override) {
                frm.set_value('base_url_override', 'https://token-plan-cn.xiaomimimo.com/v1');
            }
        } else if (p.includes('openai') || p.includes('chatgpt')) {
            frm.set_value('default_chat_model', 'gpt-5-mini');
        } else if (p.includes('gemini') || p.includes('google')) {
            frm.set_value('default_chat_model', 'gemini-3.5-flash');
        } else if (p.includes('glm') || p.includes('zhipu')) {
            frm.set_value('default_chat_model', 'glm-4.5-flash');
        }
    }
});
