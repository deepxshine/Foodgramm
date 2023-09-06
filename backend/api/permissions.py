from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticatedOrReadOnly)


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    # def has_permission(self, request, view):
    #     return request.user.is_authenticated or request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.method in SAFE_METHODS
