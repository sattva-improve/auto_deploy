"""
タスク管理API - URLルーティング
"""
from django.urls import path, include
from rest_framework_nested import routers

from .views import (
    RegisterView, LoginView, RefreshTokenView, LogoutView, MeView,
    ProjectViewSet, TaskViewSet, CommentViewSet,
)

# メインルーター
router = routers.DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')

# ネストルーター - プロジェクト配下のタスク
projects_router = routers.NestedDefaultRouter(router, r'projects', lookup='project')
projects_router.register(r'tasks', TaskViewSet, basename='project-tasks')

# ネストルーター - タスク配下のコメント
tasks_router = routers.NestedDefaultRouter(projects_router, r'tasks', lookup='task')
tasks_router.register(r'comments', CommentViewSet, basename='task-comments')

urlpatterns = [
    # 認証エンドポイント
    path('auth/register', RegisterView.as_view(), name='auth-register'),
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/refresh', RefreshTokenView.as_view(), name='auth-refresh'),
    path('auth/logout', LogoutView.as_view(), name='auth-logout'),
    path('auth/me', MeView.as_view(), name='auth-me'),
    
    # プロジェクト・タスク・コメントエンドポイント
    path('', include(router.urls)),
    path('', include(projects_router.urls)),
    path('', include(tasks_router.urls)),
]
