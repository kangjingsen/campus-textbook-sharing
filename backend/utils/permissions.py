from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """仅管理员可访问"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role in ('admin', 'superadmin')


class IsSuperAdmin(BasePermission):
    """仅超级管理员可访问"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'superadmin'


class IsOwnerOrAdmin(BasePermission):
    """仅资源拥有者或管理员可操作"""
    def has_object_permission(self, request, view, obj):
        if request.user.role in ('admin', 'superadmin'):
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
