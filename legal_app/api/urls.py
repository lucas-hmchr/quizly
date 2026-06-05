from django.urls import path
from .views import PrivacyPolicyView, ImprintView

urlpatterns = [
    path('privacy/', PrivacyPolicyView.as_view(), name='privacy'),
    path('imprint/', ImprintView.as_view(), name='imprint'),
]
