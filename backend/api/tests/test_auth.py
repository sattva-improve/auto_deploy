"""
認証APIテスト
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

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
def authenticated_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.mark.django_db
class TestRegister:
    """ユーザー登録テスト"""
    
    def test_register_success(self, api_client):
        """正常な登録"""
        url = reverse('auth-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'Password123',
            'name': '新規ユーザー'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'data' in response.data
        assert response.data['data']['email'] == 'newuser@example.com'
        assert response.data['data']['name'] == '新規ユーザー'
    
    def test_register_duplicate_email(self, api_client, test_user):
        """重複メールアドレスで登録失敗"""
        url = reverse('auth-register')
        data = {
            'email': 'test@example.com',  # 既存のメールアドレス
            'password': 'Password123',
            'name': '重複ユーザー'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_short_password(self, api_client):
        """短いパスワードで登録失敗"""
        url = reverse('auth-register')
        data = {
            'email': 'short@example.com',
            'password': 'short',  # 8文字未満
            'name': 'ショート'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogin:
    """ログインテスト"""
    
    def test_login_success(self, api_client, test_user):
        """正常なログイン"""
        url = reverse('auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert 'accessToken' in response.data['data']
        assert 'refreshToken' in response.data['data']
        assert response.data['data']['tokenType'] == 'Bearer'
    
    def test_login_invalid_credentials(self, api_client, test_user):
        """不正な認証情報でログイン失敗"""
        url = reverse('auth-login')
        data = {
            'email': 'test@example.com',
            'password': 'WrongPassword'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, api_client):
        """存在しないユーザーでログイン失敗"""
        url = reverse('auth-login')
        data = {
            'email': 'nonexistent@example.com',
            'password': 'Password123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestLogout:
    """ログアウトテスト"""
    
    def test_logout_success(self, authenticated_client):
        """正常なログアウト"""
        url = reverse('auth-logout')
        response = authenticated_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_logout_unauthenticated(self, api_client):
        """未認証でログアウト失敗"""
        url = reverse('auth-logout')
        response = api_client.post(url, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestMe:
    """現在のユーザー情報取得テスト"""
    
    def test_me_success(self, authenticated_client, test_user):
        """正常に情報取得"""
        url = reverse('auth-me')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'data' in response.data
        assert response.data['data']['email'] == test_user.email
        assert response.data['data']['name'] == test_user.name
    
    def test_me_unauthenticated(self, api_client):
        """未認証で取得失敗"""
        url = reverse('auth-me')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
