from rest_framework.permissions import BasePermission

from .services import ModulePermissionService


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )


class HasModuleAccess(BasePermission):
    message = "You do not have permission to access this module."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "role", None) == "admin":
            return True

        required_module = getattr(view, "required_module", None)
        if not required_module and hasattr(view.__class__, "required_module"):
            required_module = view.__class__.required_module
        if not required_module:
            self.message = "Module access configuration is missing for this endpoint."
            return False

        return ModulePermissionService.has_module_access(
            request.user,
            required_module,
        )