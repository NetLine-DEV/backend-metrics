from rest_framework import permissions
from .models import CustomGroup

class IsAdminOrInAdminGroup(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user and request.user.is_staff:
            return True

        return (
            request.user.is_authenticated and
            CustomGroup.objects.filter(
                group__in=request.user.groups.all(), 
                group__permissions__codename='admin'
            ).exists()
        )
