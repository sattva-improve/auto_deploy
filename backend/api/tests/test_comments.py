"""
コメントAPIテスト
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.models import Project, ProjectMember, Task, Comment

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email='test@example.com',
        password='TestPass123',
        name='テストユーザー'
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email='other@example.com',
        password='TestPass123',
        name='他のユーザー'
    )


@pytest.fixture
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def test_project(db, test_user):
    project = Project.objects.create(
        name='テストプロジェクト',
        description='テスト用プロジェクト',
        owner=test_user
    )
    ProjectMember.objects.create(
        project=project,
        user=test_user,
        role='owner'
    )
    return project


@pytest.fixture
def test_task(db, test_project, test_user):
    return Task.objects.create(
        project=test_project,
        title='テストタスク',
        description='テスト用タスク',
        status='todo',
        priority='medium',
        assignee=test_user
    )


@pytest.fixture
def test_comment(db, test_task, test_user):
    return Comment.objects.create(
        task=test_task,
        user=test_user,
        content='テストコメント'
    )


@pytest.mark.django_db
class TestCommentList:
    """コメント一覧テスト"""
    
    def test_list_comments_success(self, authenticated_client, test_project, test_task, test_comment):
        """正常にコメント一覧取得"""
        url = reverse('task-comments-list', kwargs={
            'project_pk': test_project.id,
            'task_pk': test_task.id
        })
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['content'] == 'テストコメント'


@pytest.mark.django_db
class TestCommentCreate:
    """コメント作成テスト"""
    
    def test_create_comment_success(self, authenticated_client, test_project, test_task):
        """正常にコメント作成"""
        url = reverse('task-comments-list', kwargs={
            'project_pk': test_project.id,
            'task_pk': test_task.id
        })
        data = {'content': '新規コメント'}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['content'] == '新規コメント'
        assert 'task' in response.data['data']
    
    def test_create_comment_empty_content(self, authenticated_client, test_project, test_task):
        """空のコンテンツで作成失敗"""
        url = reverse('task-comments-list', kwargs={
            'project_pk': test_project.id,
            'task_pk': test_task.id
        })
        data = {'content': ''}
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCommentDelete:
    """コメント削除テスト"""
    
    def test_delete_comment_success(self, authenticated_client, test_project, test_task, test_comment):
        """正常にコメント削除（自分のコメント）"""
        url = reverse('task-comments-detail', kwargs={
            'project_pk': test_project.id,
            'task_pk': test_task.id,
            'pk': test_comment.id
        })
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_comment_forbidden(self, api_client, test_project, test_task, test_comment, other_user):
        """他のユーザーのコメント削除で失敗"""
        # 他のユーザーをプロジェクトメンバーに追加
        ProjectMember.objects.create(
            project=test_project,
            user=other_user,
            role='member'
        )
        api_client.force_authenticate(user=other_user)
        
        url = reverse('task-comments-detail', kwargs={
            'project_pk': test_project.id,
            'task_pk': test_task.id,
            'pk': test_comment.id
        })
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
