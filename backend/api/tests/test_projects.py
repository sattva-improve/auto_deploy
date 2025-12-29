"""
プロジェクトAPIテスト
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from api.models import Project, ProjectMember

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


@pytest.mark.django_db
class TestProjectList:
    """プロジェクト一覧テスト"""
    
    def test_list_projects_success(self, authenticated_client, test_project):
        """正常にプロジェクト一覧取得"""
        url = reverse('project-list')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
        assert response.data['data'][0]['name'] == 'テストプロジェクト'
    
    def test_list_projects_unauthenticated(self, api_client):
        """未認証で取得失敗"""
        url = reverse('project-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestProjectCreate:
    """プロジェクト作成テスト"""
    
    def test_create_project_success(self, authenticated_client):
        """正常にプロジェクト作成"""
        url = reverse('project-list')
        data = {
            'name': '新規プロジェクト',
            'description': '新規プロジェクトの説明'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'data' in response.data
        assert response.data['data']['name'] == '新規プロジェクト'
        assert response.data['data']['role'] == 'owner'
    
    def test_create_project_without_name(self, authenticated_client):
        """名前なしで作成失敗"""
        url = reverse('project-list')
        data = {
            'description': '説明のみ'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProjectDetail:
    """プロジェクト詳細テスト"""
    
    def test_get_project_success(self, authenticated_client, test_project):
        """正常にプロジェクト詳細取得"""
        url = reverse('project-detail', kwargs={'pk': test_project.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert response.data['data']['name'] == 'テストプロジェクト'
        assert 'members' in response.data['data']
        assert 'taskSummary' in response.data['data']


@pytest.mark.django_db
class TestProjectUpdate:
    """プロジェクト更新テスト"""
    
    def test_update_project_success(self, authenticated_client, test_project):
        """正常にプロジェクト更新"""
        url = reverse('project-detail', kwargs={'pk': test_project.id})
        data = {
            'name': '更新プロジェクト',
            'description': '更新された説明'
        }
        response = authenticated_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['data']['name'] == '更新プロジェクト'


@pytest.mark.django_db
class TestProjectDelete:
    """プロジェクト削除テスト"""
    
    def test_delete_project_success(self, authenticated_client, test_project):
        """正常にプロジェクト削除（オーナー）"""
        url = reverse('project-detail', kwargs={'pk': test_project.id})
        response = authenticated_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_delete_project_forbidden(self, api_client, other_user, test_project):
        """他のユーザーで削除失敗"""
        api_client.force_authenticate(user=other_user)
        # まずメンバーとして追加
        ProjectMember.objects.create(
            project=test_project,
            user=other_user,
            role='member'
        )
        
        url = reverse('project-detail', kwargs={'pk': test_project.id})
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestProjectMembers:
    """プロジェクトメンバー管理テスト"""
    
    def test_list_members_success(self, authenticated_client, test_project):
        """正常にメンバー一覧取得"""
        url = reverse('project-members', kwargs={'pk': test_project.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert len(response.data['data']) == 1
    
    def test_add_member_success(self, authenticated_client, test_project, other_user):
        """正常にメンバー追加"""
        url = reverse('project-members', kwargs={'pk': test_project.id})
        data = {
            'userId': str(other_user.id),
            'role': 'member'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['data']['role'] == 'member'
    
    def test_add_duplicate_member(self, authenticated_client, test_project, other_user):
        """重複メンバー追加で失敗"""
        ProjectMember.objects.create(
            project=test_project,
            user=other_user,
            role='member'
        )
        
        url = reverse('project-members', kwargs={'pk': test_project.id})
        data = {
            'userId': str(other_user.id),
            'role': 'member'
        }
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_409_CONFLICT
