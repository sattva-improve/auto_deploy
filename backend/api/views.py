"""
タスク管理API - ビュー
OpenAPI仕様書に基づくAPIエンドポイント
"""
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import Project, ProjectMember, Task, Comment
from .serializers import (
    RegisterSerializer, LoginSerializer, RefreshTokenSerializer,
    UserResponseSerializer, UserDetailSerializer,
    CreateProjectSerializer, UpdateProjectSerializer, ProjectSerializer, ProjectDetailSerializer,
    AddMemberSerializer, ProjectMemberSerializer,
    CreateTaskSerializer, UpdateTaskSerializer, TaskSerializer, TaskResponseSerializer, TaskDetailSerializer,
    CreateCommentSerializer, CommentSerializer, CommentResponseSerializer,
)
from .pagination import CustomPagination
from .permissions import IsProjectMember, IsProjectAdmin, IsProjectOwner

User = get_user_model()


# ============================================
# 認証 API
# ============================================
class RegisterView(generics.CreateAPIView):
    """ユーザー登録"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        response_serializer = UserResponseSerializer(user)
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """ログイン"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'data': {
                'accessToken': str(refresh.access_token),
                'refreshToken': str(refresh),
                'expiresIn': 3600,
                'tokenType': 'Bearer',
            }
        })


class RefreshTokenView(APIView):
    """トークンリフレッシュ"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            refresh = RefreshToken(serializer.validated_data['refreshToken'])
            return Response({
                'data': {
                    'accessToken': str(refresh.access_token),
                    'refreshToken': str(refresh),
                    'expiresIn': 3600,
                    'tokenType': 'Bearer',
                }
            })
        except TokenError:
            return Response(
                {'error': {'code': 'AUTH_001', 'message': '無効なトークンです'}},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(APIView):
    """ログアウト"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refreshToken')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except TokenError:
            pass
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """現在のユーザー情報取得"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserResponseSerializer(request.user)
        return Response({'data': serializer.data})


# ============================================
# プロジェクト API
# ============================================
class ProjectViewSet(viewsets.ModelViewSet):
    """プロジェクトビューセット"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateProjectSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateProjectSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        return ProjectSerializer
    
    def get_queryset(self):
        user = self.request.user
        # ユーザーが参加しているプロジェクトを取得
        owned_projects = Project.objects.filter(owner=user)
        member_projects = Project.objects.filter(members__user=user)
        return (owned_projects | member_projects).distinct().select_related('owner')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # プロジェクト作成時にオーナーを設定
        project = serializer.save(owner=request.user)
        
        # オーナーをメンバーとして追加
        ProjectMember.objects.create(
            project=project,
            user=request.user,
            role='owner'
        )
        
        response_serializer = ProjectSerializer(project, context={'request': request})
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data})
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        response_serializer = ProjectSerializer(instance, context={'request': request})
        return Response({'data': response_serializer.data})
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # オーナーのみ削除可能
        if instance.owner != request.user:
            return Response(
                {'error': {'code': 'AUTHZ_001', 'message': 'プロジェクトの削除権限がありません'}},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get', 'post'], url_path='members')
    def members(self, request, pk=None):
        """メンバー一覧取得・追加"""
        project = self.get_object()
        
        if request.method == 'GET':
            members = project.members.select_related('user').all()
            serializer = ProjectMemberSerializer(members, many=True)
            return Response({'data': serializer.data})
        
        elif request.method == 'POST':
            # 管理者以上のみメンバー追加可能
            membership = project.members.filter(user=request.user).first()
            if not (project.owner == request.user or 
                    (membership and membership.role in ['owner', 'admin'])):
                return Response(
                    {'error': {'code': 'AUTHZ_001', 'message': 'メンバー追加権限がありません'}},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            serializer = AddMemberSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user_id = serializer.validated_data['userId']
            role = serializer.validated_data.get('role', 'member')
            
            # 既にメンバーか確認
            if project.members.filter(user_id=user_id).exists():
                return Response(
                    {'error': {'code': 'RES_002', 'message': 'このユーザーは既にメンバーです'}},
                    status=status.HTTP_409_CONFLICT
                )
            
            user = User.objects.get(id=user_id)
            member = ProjectMember.objects.create(
                project=project,
                user=user,
                role=role
            )
            
            response_serializer = ProjectMemberSerializer(member)
            return Response(
                {'data': response_serializer.data},
                status=status.HTTP_201_CREATED
            )
    
    @action(detail=True, methods=['delete'], url_path='members/(?P<user_id>[^/.]+)')
    def remove_member(self, request, pk=None, user_id=None):
        """メンバー削除"""
        project = self.get_object()
        
        # 管理者以上のみメンバー削除可能
        membership = project.members.filter(user=request.user).first()
        if not (project.owner == request.user or 
                (membership and membership.role in ['owner', 'admin'])):
            return Response(
                {'error': {'code': 'AUTHZ_001', 'message': 'メンバー削除権限がありません'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # オーナーは削除不可
        if str(project.owner.id) == user_id:
            return Response(
                {'error': {'code': 'AUTHZ_001', 'message': 'オーナーは削除できません'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        member = get_object_or_404(ProjectMember, project=project, user_id=user_id)
        member.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================
# タスク API
# ============================================
class TaskViewSet(viewsets.ModelViewSet):
    """タスクビューセット"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateTaskSerializer
        elif self.action in ['update', 'partial_update']:
            return UpdateTaskSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        return TaskSerializer
    
    def get_queryset(self):
        project_id = self.kwargs.get('project_pk')
        queryset = Task.objects.filter(project_id=project_id).select_related('assignee', 'project')
        
        # フィルター
        status_param = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        assignee_id = self.request.query_params.get('assigneeId')
        
        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assignee_id:
            queryset = queryset.filter(assignee_id=assignee_id)
        
        # ソート
        sort = self.request.query_params.get('sort', 'createdAt')
        order = self.request.query_params.get('order', 'desc')
        
        sort_field_mapping = {
            'createdAt': 'created_at',
            'updatedAt': 'updated_at',
            'dueDate': 'due_date',
            'priority': 'priority',
            'status': 'status',
        }
        
        sort_field = sort_field_mapping.get(sort, 'created_at')
        if order == 'desc':
            sort_field = f'-{sort_field}'
        
        return queryset.order_by(sort_field)
    
    def create(self, request, *args, **kwargs):
        project_id = self.kwargs.get('project_pk')
        project = get_object_or_404(Project, id=project_id)
        
        # プロジェクトメンバーか確認
        if not self._is_project_member(project, request.user):
            return Response(
                {'error': {'code': 'AUTHZ_001', 'message': 'このプロジェクトへのアクセス権限がありません'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(project=project)
        
        response_serializer = TaskResponseSerializer(task)
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'data': serializer.data})
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        response_serializer = TaskResponseSerializer(instance)
        return Response({'data': response_serializer.data})
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, project_pk=None, pk=None):
        """タスクステータス更新"""
        task = self.get_object()
        
        new_status = request.data.get('status')
        if new_status not in ['todo', 'in_progress', 'done']:
            return Response(
                {'error': {'code': 'VAL_001', 'message': '無効なステータスです'}},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        task.status = new_status
        task.save()
        
        serializer = TaskResponseSerializer(task)
        return Response({'data': serializer.data})
    
    def _is_project_member(self, project, user):
        """ユーザーがプロジェクトメンバーか確認"""
        return (project.owner == user or 
                project.members.filter(user=user).exists())


# ============================================
# コメント API
# ============================================
class CommentViewSet(viewsets.ModelViewSet):
    """コメントビューセット"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    http_method_names = ['get', 'post', 'delete']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCommentSerializer
        return CommentSerializer
    
    def get_queryset(self):
        task_id = self.kwargs.get('task_pk')
        return Comment.objects.filter(task_id=task_id).select_related('user')
    
    def create(self, request, *args, **kwargs):
        task_id = self.kwargs.get('task_pk')
        task = get_object_or_404(Task, id=task_id)
        
        # プロジェクトメンバーか確認
        project = task.project
        if not self._is_project_member(project, request.user):
            return Response(
                {'error': {'code': 'AUTHZ_001', 'message': 'このタスクへのアクセス権限がありません'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, user=request.user)
        
        response_serializer = CommentResponseSerializer(comment)
        return Response(
            {'data': response_serializer.data},
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 自分のコメントのみ削除可能
        if instance.user != request.user:
            return Response(
                {'error': {'code': 'AUTHZ_001', 'message': 'このコメントの削除権限がありません'}},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def _is_project_member(self, project, user):
        """ユーザーがプロジェクトメンバーか確認"""
        return (project.owner == user or 
                project.members.filter(user=user).exists())
