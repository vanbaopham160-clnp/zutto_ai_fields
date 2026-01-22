// Form hook - triggers AI button initialization
$(document).on('form-load form-refresh', function() {
    setTimeout(function() {
        if (cur_frm && typeof zutto_ai_fields !== 'undefined' && zutto_ai_fields.init_for_form) {
            zutto_ai_fields.init_for_form(cur_frm);
        }
    }, 500);
});
