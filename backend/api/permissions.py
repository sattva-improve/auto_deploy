"""
タスク管理API - カスタムパーミッション
"""
from rest_framework import permissions


class IsProjectMember(permissions.BasePermission):
    """プロジェクトメンバーかどうかを確認"""
    
    def has_object_permission(self, request, view, obj):
        project = getattr(obj, 'project', obj)
        return (
            project.owner == request.user or
            project.members.filter(user=request.user).exists()
        )


class IsProjectAdmin(permissions.BasePermission):
    """プロジェクト管理者かどうかを確認"""
    
    def has_object_permission(self, request, view, obj):
        project = getattr(obj, 'project', obj)
        if project.owner == request.user:
            return True
        membership = project.members.filter(user=request.user).first()
        return membership and membership.role in ['owner', 'admin']


class IsProjectOwner(permissions.BasePermission):
    """プロジェクトオーナーかどうかを確認"""
    
    def has_object_permission(self, request, view, obj):
        project = getattr(obj, 'project', obj)
        return project.owner == request.user
