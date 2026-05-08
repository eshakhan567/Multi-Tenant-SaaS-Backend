from audit.models import AuditLog


# This function is used to create audit log entries
def log_audit(user, action, model_name, object_id, object_repr, changes=None, request=None):
    """Helper function to create audit log entries"""
    ip_address = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
    
    AuditLog.objects.create(
        company=user.company,
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        changes=changes or {},
        ip_address=ip_address
    )
