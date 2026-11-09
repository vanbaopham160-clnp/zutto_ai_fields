import frappe

def has_provider_permission(doc, user=None, ptype=None):
    """Check if user has permission for Zutto AI Provider (System Manager only)"""
    if not user:
        user = frappe.session.user

    return "System Manager" in frappe.get_roles(user)

def has_settings_permission(doc, user=None, ptype=None):
    """Backward compatibility alias for has_provider_permission"""
    return has_provider_permission(doc, user=user, ptype=ptype)

def has_config_permission(doc, user=None, ptype=None):
    """Check if user has permission for AI Field Config"""
    if not user:
        user = frappe.session.user

    if "System Manager" in frappe.get_roles(user):
        return True

    return frappe.has_permission("AI Field Config", ptype=ptype, user=user)
