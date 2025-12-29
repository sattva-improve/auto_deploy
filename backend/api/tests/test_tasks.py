"""
タスクAPIテスト
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.models import Project, ProjectMember, Task

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


@pytest.mark.django_db
class TestTaskList:
    """タスク一覧テスト"""
    
    def test_list_tasks_success(self, authenticated_client, test_project, test_task):
        """正常にタスク一覧取得"""
        url = reverse('project-tasks-list', kwargs={'project_pk': test_project.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['title'] == 'テストタスク'
    
    def test_list_tasks_filter_by_status(self, authenticated_client, test_project, test_task):
        """ステータスフィルター"""
        url = reverse('project-tasks-list', kwargs={'project_pk': test_project.id})
        response = authenticated_client.get(url, {'status': 'todo'})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['data']) == 1
        
        response = authenticated_client.get(url, {'status': 'done'})
        assert len(response.data['data']) == 0


@pytest.mark.django_db
class TestTaskCreate:
    """タスク作成テスト"""
    
    def test_create_task_success(self, authenticated_client, test_project):
        """正常にタスク作成"""
        url = reverse('project-tasks-list', kwargs={'project_pk': test_project.id})
        data = {
            'title': '新規タスク',
            'description': '新規タスクの説明',
            'priority': 'high'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['title'] == '新規タスク'
        assert response.data['data']['status'] == 'todo'
        assert response.data['data']['priority'] == 'high'
    
    def test_create_task_with_assignee(self, authenticated_client, test_project, test_user):
        """担当者付きタスク作成"""
        url = reverse('project-tasks-list', kwargs={'project_pk': test_project.id})
        data = {
            'title': '担当者付きタスク',
            'assigneeId': str(test_user.id)
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['assignee']['id'] == str(test_user.id)


@pytest.mark.django_db
class TestTaskDetail:
    """タスク詳細テスト"""
    
    def test_get_task_success(self, authenticated_client, test_project, test_task):
        """正常にタスク詳細取得"""
        url = reverse('project-tasks-detail', kwargs={
            'project_pk': test_project.id,
            'pk': test_task.id
        })
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['title'] == 'テストタスク'
        assert 'project' in response.data['data']
        assert 'comments' in response.data['data']


@pytest.mark.django_db
class TestTaskUpdate:
    """タスク更新テスト"""
    
    def test_update_task_success(self, authenticated_client, test_project, test_task):
        """正常にタスク更新"""
        url = reverse('project-tasks-detail', kwargs={
            'project_pk': test_project.id,
            'pk': test_task.id
        })
        data = {
            'title': '更新タスク',
            'status': 'in_progress'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['title'] == '更新タスク'
        assert response.data['data']['status'] == 'in_progress'


@pytest.mark.django_db
class TestTaskStatusUpdate:
    """タスクステータス更新テスト"""
    
    def test_update_status_success(self, authenticated_client, test_project, test_task):
        """正常にステータス更新"""
        url = reverse('project-tasks-update-status', kwargs={
            'project_pk': test_project.id,
            'pk': test_task.id
        })
        data = {'status': 'done'}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['status'] == 'done'
    
    def test_update_status_invalid(self, authenticated_client, test_project, test_task):
        """無効なステータスで失敗"""
        url = reverse('project-tasks-update-status', kwargs={
            'project_pk': test_project.id,
            'pk': test_task.id
        })
        data = {'status': 'invalid_status'}
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestTaskDelete:
    """タスク削除テスト"""
    
    def test_delete_task_success(self, authenticated_client, test_project, test_task):
        """正常にタスク削除"""
        url = reverse('project-tasks-detail', kwargs={
            'project_pk': test_project.id,
            'pk': test_task.id
        })
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
