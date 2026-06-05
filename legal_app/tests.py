import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

@pytest.mark.django_db
class TestLegal:
    def setup_method(self):
        self.client = APIClient()

    def test_privacy_policy(self):
        url = reverse('privacy')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "Privacy Policy" in response.data['title']

    def test_imprint(self):
        url = reverse('imprint')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "Imprint" in response.data['title']
