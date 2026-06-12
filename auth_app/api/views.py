from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, UserSerializer

def set_auth_cookies(response, tokens):
    """Set JWT tokens in HttpOnly cookies."""
    common_opts = {
        'httponly': True,
        'secure': not settings.DEBUG,
        'samesite': 'Lax'
    }
    response.set_cookie('access_token', tokens['access'], **common_opts)
    response.set_cookie('refresh_token', tokens['refresh'], **common_opts)

class RegisterView(APIView):
    """API View for user registration."""
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "User created successfully!"}, status=201)
        return Response(serializer.errors, status=400)

class LoginView(TokenObtainPairView):
    """API View for user login."""
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        user = authenticate(
            username=request.data.get('username'),
            password=request.data.get('password')
        )
        if user:
            refresh = RefreshToken.for_user(user)
            tokens = {'refresh': str(refresh), 'access': str(refresh.access_token)}
            response = Response(
                {"detail": "Login successfully!", "user": {"id": user.id, "username": user.username, "email": user.email}},
                status=200
            )
            set_auth_cookies(response, tokens)
            return response
        return Response({"detail": "Invalid credentials"}, status=401)

class UserView(APIView):
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class LogoutView(APIView):
    """API View for user logout."""
    def post(self, request):
        response = Response({"message": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."})
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh_token')
        if refresh is None :
            return Response({"detail": "Refresh token is missing."},
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data={"refresh": refresh})
        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response({"detail": "Refresh token invalid!"}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get("access")
        response = Response({"message": "access token refreshed successfully."})
        response.set_cookie(
            key='access_token',
            value=access_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        return response