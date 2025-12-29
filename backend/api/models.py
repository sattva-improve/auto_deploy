"""
タスク管理API - モデル定義
OpenAPI仕様書に基づくDjangoモデル
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    """カスタムユーザーマネージャー"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('メールアドレスは必須です')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """ユーザーモデル"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # メールアドレスでログインするため不要
    email = models.EmailField('メールアドレス', max_length=255, unique=True)
    name = models.CharField('ユーザー名', max_length=100)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'
    
    def __str__(self):
        return self.email


class Project(models.Model):
    """プロジェクトモデル"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('プロジェクト名', max_length=100)
    description = models.TextField('説明', max_length=1000, blank=True, default='')
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_projects',
        verbose_name='オーナー'
    )
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'プロジェクト'
        verbose_name_plural = 'プロジェクト'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def task_count(self):
        """タスク数を取得"""
        return self.tasks.count()
    
    def get_task_summary(self):
        """タスクサマリーを取得"""
        tasks = self.tasks.all()
        return {
            'total': tasks.count(),
            'todo': tasks.filter(status='todo').count(),
            'in_progress': tasks.filter(status='in_progress').count(),
            'done': tasks.filter(status='done').count(),
        }


class ProjectMember(models.Model):
    """プロジェクトメンバーモデル"""
    ROLE_CHOICES = [
        ('owner', 'オーナー'),
        ('admin', '管理者'),
        ('member', 'メンバー'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name='プロジェクト'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_memberships',
        verbose_name='ユーザー'
    )
    role = models.CharField('ロール', max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField('参加日時', auto_now_add=True)
    
    class Meta:
        db_table = 'project_members'
        verbose_name = 'プロジェクトメンバー'
        verbose_name_plural = 'プロジェクトメンバー'
        unique_together = ['project', 'user']
    
    def __str__(self):
        return f'{self.user.name} - {self.project.name} ({self.role})'


class Task(models.Model):
    """タスクモデル"""
    STATUS_CHOICES = [
        ('todo', 'TODO'),
        ('in_progress', '進行中'),
        ('done', '完了'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name='プロジェクト'
    )
    title = models.CharField('タイトル', max_length=100)
    description = models.TextField('説明', max_length=1000, blank=True, default='')
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField('優先度', max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField('期限', null=True, blank=True)
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        verbose_name='担当者'
    )
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'タスク'
        verbose_name_plural = 'タスク'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def comment_count(self):
        """コメント数を取得"""
        return self.comments.count()


class Comment(models.Model):
    """コメントモデル"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='タスク'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='ユーザー'
    )
    content = models.TextField('内容', max_length=1000)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    
    class Meta:
        db_table = 'comments'
        verbose_name = 'コメント'
        verbose_name_plural = 'コメント'
        ordering = ['created_at']
    
    def __str__(self):
        return f'{self.user.name}: {self.content[:50]}'

