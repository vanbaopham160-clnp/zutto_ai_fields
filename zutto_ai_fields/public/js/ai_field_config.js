frappe.ui.form.on('AI Field Config', {
	refresh: function(frm) {
		// Filter provider to active Zutto AI Providers
		frm.set_query('provider', function() {
			return {
				filters: {
					active: 1
				}
			};
		});

		// Update placeholder help when form loads
		if (frm.doc.prompt_template) {
			update_placeholder_help(frm);
		}
	},

	prompt_template: function(frm) {
		// Update placeholder help when prompt changes
		update_placeholder_help(frm);
	},

	// Handle the button FIELD click
	test_generation: function(frm) {
		test_generation(frm);
	}
});

function update_placeholder_help(frm) {
	if (!frm.doc.prompt_template) {
		frm.set_df_property('placeholder_help', 'options', '');
		return;
	}

	// Extract placeholders from template
	const placeholders = frm.doc.prompt_template.match(/\{\{(\w+)\}\}/g) || [];
	const uniquePlaceholders = [...new Set(placeholders.map(p => p.replace(/\{\{|\}\}/g, '')))];

	if (uniquePlaceholders.length === 0) {
		frm.set_df_property('placeholder_help', 'options',
			'<div class="text-muted">No placeholders found. Use {{field_name}} to reference document fields.</div>'
		);
		return;
	}

	let html = '<div style="margin-top: 10px; padding: 10px; background: #f9f9f9; border-radius: 5px;">';
	html += '<strong>Placeholders found:</strong><br>';
	uniquePlaceholders.forEach(p => {
		html += `<code>{{${p}}}</code><br>`;
	});
	html += '</div>';

	frm.set_df_property('placeholder_help', 'options', html);
}

function test_generation(frm) {
	if (!frm.doc.enabled) {
		frappe.show_alert({
			message: __('Please enable this config first.'),
			indicator: 'red'
		}, 5);
		return;
	}

	if (!frm.doc.prompt_template) {
		frappe.show_alert({
			message: __('Please add a prompt template first.'),
			indicator: 'red'
		}, 5);
		return;
	}

	if (frm.is_new()) {
		frappe.show_alert({
			message: __('Please save the document first.'),
			indicator: 'red'
		}, 5);
		return;
	}

	frappe.show_alert({
		message: __('Testing generation...'),
		indicator: 'blue'
	}, 10);

	frappe.call({
		method: 'zutto_ai_fields.api.test_ai_field_config',
		args: {
			config_name: frm.doc.name
		},
		callback: function(r) {
			const result = r.message;

			if (result && result.success) {
				frappe.msgprint({
					title: __('Test Generation Successful'),
					indicator: 'green',
					message: `<strong>Provider:</strong> ${result.provider || 'default'}<br>
							  <strong>Model:</strong> ${result.model || 'default'}<br><br>
							  <strong>Generated Content:</strong><br>
							  <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 10px; border-radius: 5px;">${frappe.utils.escape_html(result.message || result.content || '')}</pre>`
				});
			} else {
				frappe.msgprint({
					title: __('Test Generation Failed'),
					indicator: 'red',
					message: result ? (result.error || __('Unknown error')) : __('Unknown error')
				});
			}
		}
	});
}
