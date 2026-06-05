from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

class PrivacyPolicyView(APIView):
    """
    API View for Privacy Policy.
    """
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            "title": "Privacy Policy",
            "content": "This is a placeholder for the privacy policy. Please update with your actual data."
        })

class ImprintView(APIView):
    """
    API View for Imprint.
    """
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        return Response({
            "title": "Imprint",
            "content": "This is a placeholder for the imprint. Please update with your actual data."
        })
