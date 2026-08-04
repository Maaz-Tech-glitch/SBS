from rest_framework.permissions import BasePermission


#  permission only admin or shopkeeper
class IsAdminOrShopkeeper(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ["admin", "shopkeeper"]
    
# permission only for admin to delete
class IsAdminForDelete(BasePermission):
    def has_permission(self, request, view):
        if request.method == "DELETE":
            return request.user.role == "admin"
        return True