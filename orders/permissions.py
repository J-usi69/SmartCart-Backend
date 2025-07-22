from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAdminOrAssignedDelivery(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in SAFE_METHODS:
            return (
                obj.client == user or
                user.is_staff or user.is_superuser or
                obj.delivery_user == user
            )


        return (
            obj.client == user or
            user.is_staff or user.is_superuser or
            obj.delivery_user == user
        )

class IsCartOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.cart.user == request.user