"""Модуль разрешений."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешение создавать, изменять и удалять данные только их автору."""

    def has_object_permission(self, request, view, obj):
        """Разрешения на уровне объектов."""
        return (
            request.method in SAFE_METHODS
            or obj.author == request.user
        )
