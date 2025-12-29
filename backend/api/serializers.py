"""
タスク管理API - シリアライザー
OpenAPI仕様書に基づくDRFシリアライザー
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Project, ProjectMember, Task, Comment

User = get_user_model()


# ============================================
# 認証関連シリアライザー
# ============================================
class RegisterSerializer(serializers.ModelSerializer):
    """ユーザー登録シリアライザー"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password]
    )
    
    class Meta:
        model = User
        fields = ['email', 'password', 'name']
    
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name']
        )
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """ログインシリアライザー"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['name'] = user.name
        token['email'] = user.email
        return token


class RefreshTokenSerializer(serializers.Serializer):
    """トークンリフレッシュシリアライザー"""
    refreshToken = serializers.CharField(required=True)


# ============================================
# ユーザー関連シリアライザー
# ============================================
class UserSummarySerializer(serializers.ModelSerializer):
    """ユーザーサマリーシリアライザー"""
    class Meta:
        model = User
        fields = ['id', 'name']


class UserDetailSerializer(serializers.ModelSerializer):
    """ユーザー詳細シリアライザー"""
    class Meta:
        model = User
        fields = ['id', 'name', 'email']


class UserResponseSerializer(serializers.ModelSerializer):
    """ユーザーレスポンスシリアライザー"""
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    created_at = serializers.DateTimeField(source='date_joined', read_only=True)


# ============================================
# プロジェクト関連シリアライザー
# ============================================
class CreateProjectSerializer(serializers.ModelSerializer):
    """プロジェクト作成シリアライザー"""
    class Meta:
        model = Project
        fields = ['name', 'description']


class UpdateProjectSerializer(serializers.ModelSerializer):
    """プロジェクト更新シリアライザー"""
    class Meta:
        model = Project
        fields = ['name', 'description']
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
        }


class ProjectSerializer(serializers.ModelSerializer):
    """プロジェクトシリアライザー"""
    owner = UserSummarySerializer(read_only=True)
    role = serializers.SerializerMethodField()
    taskCount = serializers.IntegerField(source='task_count', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'role', 'taskCount', 'createdAt', 'updatedAt']
        read_only_fields = ['id', 'createdAt', 'updatedAt']
    
    def get_role(self, obj):
        request = self.context.get('request')
        if request and request.user:
            if obj.owner == request.user:
                return 'owner'
            membership = obj.members.filter(user=request.user).first()
            if membership:
                return membership.role
        return None


class ProjectDetailSerializer(ProjectSerializer):
    """プロジェクト詳細シリアライザー"""
    members = serializers.SerializerMethodField()
    taskSummary = serializers.SerializerMethodField()
    
    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ['members', 'taskSummary']
    
    def get_members(self, obj):
        members = obj.members.select_related('user').all()
        return ProjectMemberSerializer(members, many=True).data
    
    def get_taskSummary(self, obj):
        return obj.get_task_summary()


# ============================================
# プロジェクトメンバー関連シリアライザー
# ============================================
class AddMemberSerializer(serializers.Serializer):
    """メンバー追加シリアライザー"""
    userId = serializers.UUIDField(required=True)
    role = serializers.ChoiceField(
        choices=['admin', 'member'],
        default='member',
        required=False
    )
    
    def validate_userId(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('指定されたユーザーが存在しません')
        return value


class ProjectMemberSerializer(serializers.ModelSerializer):
    """プロジェクトメンバーシリアライザー"""
    id = serializers.UUIDField(source='user.id', read_only=True)
    name = serializers.CharField(source='user.name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'name', 'email', 'role']


# ============================================
# タスク関連シリアライザー
# ============================================
class CreateTaskSerializer(serializers.ModelSerializer):
    """タスク作成シリアライザー"""
    assigneeId = serializers.UUIDField(required=False, allow_null=True)
    dueDate = serializers.DateTimeField(source='due_date', required=False, allow_null=True)
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'dueDate', 'assigneeId']
        extra_kwargs = {
            'status': {'default': 'todo'},
            'priority': {'default': 'medium'},
        }
    
    def validate_assigneeId(self, value):
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('指定されたユーザーが存在しません')
        return value
    
    def create(self, validated_data):
        assignee_id = validated_data.pop('assigneeId', None)
        if assignee_id:
            validated_data['assignee'] = User.objects.get(id=assignee_id)
        return super().create(validated_data)


class UpdateTaskSerializer(serializers.ModelSerializer):
    """タスク更新シリアライザー"""
    assigneeId = serializers.UUIDField(required=False, allow_null=True)
    dueDate = serializers.DateTimeField(source='due_date', required=False, allow_null=True)
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'dueDate', 'assigneeId']
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
            'status': {'required': False},
            'priority': {'required': False},
        }
    
    def validate_assigneeId(self, value):
        if value and not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('指定されたユーザーが存在しません')
        return value
    
    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assigneeId', None)
        if assignee_id is not None:
            validated_data['assignee'] = User.objects.get(id=assignee_id) if assignee_id else None
        return super().update(instance, validated_data)


class TaskSerializer(serializers.ModelSerializer):
    """タスクシリアライザー"""
    assignee = UserSummarySerializer(read_only=True)
    commentCount = serializers.IntegerField(source='comment_count', read_only=True)
    dueDate = serializers.DateTimeField(source='due_date', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    updatedAt = serializers.DateTimeField(source='updated_at', read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'priority',
            'dueDate', 'assignee', 'commentCount', 'createdAt', 'updatedAt'
        ]
        read_only_fields = ['id', 'createdAt', 'updatedAt']


class TaskResponseSerializer(TaskSerializer):
    """タスクレスポンスシリアライザー（プロジェクト情報付き）"""
    project = serializers.SerializerMethodField()
    
    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ['project']
    
    def get_project(self, obj):
        return {
            'id': str(obj.project.id),
            'name': obj.project.name
        }


class TaskDetailSerializer(TaskResponseSerializer):
    """タスク詳細シリアライザー（コメント付き）"""
    comments = serializers.SerializerMethodField()
    
    class Meta(TaskResponseSerializer.Meta):
        fields = TaskResponseSerializer.Meta.fields + ['comments']
    
    def get_comments(self, obj):
        comments = obj.comments.select_related('user').all()
        return CommentSerializer(comments, many=True).data


# ============================================
# コメント関連シリアライザー
# ============================================
class CreateCommentSerializer(serializers.ModelSerializer):
    """コメント作成シリアライザー"""
    class Meta:
        model = Comment
        fields = ['content']


class CommentSerializer(serializers.ModelSerializer):
    """コメントシリアライザー"""
    user = UserSummarySerializer(read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'content', 'user', 'createdAt']
        read_only_fields = ['id', 'createdAt']


class CommentResponseSerializer(CommentSerializer):
    """コメントレスポンスシリアライザー（タスク情報付き）"""
    task = serializers.SerializerMethodField()
    
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['task']
    
    def get_task(self, obj):
        return {
            'id': str(obj.task.id),
            'title': obj.task.title
        }


# ============================================
# レスポンスラッパーシリアライザー
# ============================================
class DataResponseSerializer(serializers.Serializer):
    """データラッパーシリアライザー"""
    data = serializers.JSONField()


class TokenResponseSerializer(serializers.Serializer):
    """トークンレスポンスシリアライザー"""
    accessToken = serializers.CharField()
    refreshToken = serializers.CharField()
    expiresIn = serializers.IntegerField()
    tokenType = serializers.CharField(default='Bearer')
