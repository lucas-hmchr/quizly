import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestAuth:
    def setup_method(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
        self.logout_url = reverse('logout')
        self.user_url = reverse('user')

    def test_register_user(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123"
        }
        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="testuser").exists()

    def test_register_user_mismatch_password(self):
        data = {
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "testpassword123",
            "password_confirm": "wrongpassword"
        }
        response = self.client.post(self.register_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_user(self):
        User.objects.create_user(username="loginuser", password="password123")
        data = {"username": "loginuser", "password": "password123"}
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_200_OK
        assert 'access_token' in response.cookies
        assert 'refresh_token' in response.cookies

    def test_login_user_invalid(self):
        data = {"username": "wrong", "password": "wrong"}
        response = self.client.post(self.login_url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_user(self):
        user = User.objects.create_user(username="logoutuser", password="password123")
        self.client.force_authenticate(user=user)
        # Mock cookies
        self.client.cookies['refresh_token'] = 'dummy'
        response = self.client.post(self.logout_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.cookies['access_token'].value == ''
        assert response.cookies['refresh_token'].value == ''

    def test_get_user_info(self):
        user = User.objects.create_user(username="infouser", password="password123")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.user_url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == "infouser"
