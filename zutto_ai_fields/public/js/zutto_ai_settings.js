frappe.ui.form.on('Zutto AI Settings', {
	refresh: function(frm) {
		// Optional: Also add to Actions menu
		frm.add_custom_button(__('Test Connection'), function() {
			test_connection(frm);
		}, __('Actions'));
	},

	// Handle the button FIELD click
	test_connection: function(frm) {
		test_connection(frm);
	}
});

function test_connection(frm) {
	// Check if AI is enabled
	if (!frm.doc.enabled) {
		frappe.show_alert({
			message: __('AI generation is disabled. Please enable it first.'),
			indicator: 'red'
		}, 5);
		return;
	}

	// Check if default provider is selected
	if (!frm.doc.default_provider) {
		frappe.show_alert({
			message: __('Please select a default provider first.'),
			indicator: 'red'
		}, 5);
		return;
	}

	// Check if API key is configured (except for Ollama)
	if (frm.doc.default_provider !== 'ollama') {
		const apiKeyField = frm.doc.default_provider === 'openai' ? 'openai_api_key' : 'gemini_api_key';
		if (!frm.doc[apiKeyField]) {
			frappe.show_alert({
				message: __('Please configure the API key for {0} first.', [frm.doc.default_provider]),
				indicator: 'red'
			}, 5);
			return;
		}
	}

	// Show loading state
	frappe.show_alert({
		message: __('Testing connection...'),
		indicator: 'blue'
	}, 10);

	// Call backend to test connection
	frappe.call({
		method: 'zutto_ai_fields.api.test_connection',
		args: {
			provider: frm.doc.default_provider
		},
		callback: function(r) {
			const result = r.message;

			if (result.success) {
				// Show success message
				frappe.show_alert({
					message: result.message || __('Connection successful!'),
					indicator: 'green'
				}, 10);

				// Show in dialog for better visibility
				frappe.msgprint({
					title: __('Connection Test'),
					indicator: 'green',
					message: result.message
				});
			} else {
				// Show error message
				let error_msg = result.error;

				// Map error types to user-friendly messages
				const errorMessages = {
					'invalid_key': __('API key not configured or invalid. Please check settings.'),
					'rate_limit': __('Rate limit exceeded. Please try again later.'),
					'timeout': __('Request timed out. Please try again.'),
					'api_error': __('API error occurred. Please check logs.'),
					'disabled': __('AI generation is disabled in settings.'),
					'permission': __('You do not have permission to use AI generation.'),
					'not_found': __('AI Field Config not found.'),
					'unknown': __('An unexpected error occurred.')
				};

				if (errorMessages[result.error_type]) {
					error_msg = errorMessages[result.error_type];
				}

				frappe.show_alert({
					message: error_msg,
					indicator: 'red'
				}, 10);

				// Show in dialog for better visibility
				frappe.msgprint({
					title: __('Connection Test Failed'),
					indicator: 'red',
					message: error_msg
				});
			}
		},
		error: function() {
			frappe.show_alert({
				message: __('Failed to test connection. Please try again.'),
				indicator: 'red'
			}, 5);
		}
	});
}