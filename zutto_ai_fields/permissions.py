import frappe

def has_settings_permission(doc, user=None, ptype=None):
    """Check if user has permission for Zutto AI Settings"""
    if not user:
        user = frappe.session.user

    # Only System Managers can access settings
    return "System Manager" in frappe.get_roles(user)

def has_config_permission(doc, user=None, ptype=None):
    """Check if user has permission for AI Field Config"""
    if not user:
        user = frappe.session.user

    # System Managers and users with AI Field Config permission
    if "System Manager" in frappe.get_roles(user):
        return True

    # Check if user has specific permission
    return frappe.has_permission("AI Field Config", ptype=ptype, user=user)