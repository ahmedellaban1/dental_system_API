"""
=============================================================================
accounts/auth_views.py - JWT Authentication Views
=============================================================================
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    TokenObtainSerializer,
    TokenRefreshSerializer,
    UserWithTokenSerializer,
    UserDetailSerializer
)
from etc.responses import success, created, bad_request, unauthorized


class LoginView(APIView):
    """
    POST: Login user and return JWT tokens
    """
    permission_classes = [AllowAny]
    serializer_class = TokenObtainSerializer

    def post(self, request):
        serializer = TokenObtainSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            # Get user data with tokens
            user_serializer = UserWithTokenSerializer(user)

            return success(
                message=f"مرحباً {user.first_name}! تم تسجيل الدخول بنجاح / Welcome! Login successful",
                data=user_serializer.data
            )

        return bad_request(
            message="فشل تسجيل الدخول / Login failed",
            errors=serializer.errors
        )


class LogoutView(APIView):
    """
    POST: Logout user by blacklisting refresh token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')

            if not refresh_token:
                return bad_request(
                    message="رمز التحديث مطلوب / Refresh token is required"
                )

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            return success(
                message="تم تسجيل الخروج بنجاح / Logout successful"
            )

        except TokenError:
            return bad_request(
                message="رمز غير صالح / Invalid token"
            )
        except Exception as e:
            return bad_request(
                message=f"فشل تسجيل الخروج / Logout failed: {str(e)}"
            )


class RefreshTokenView(APIView):
    """
    POST: Refresh access token using refresh token
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)

        if serializer.is_valid():
            return success(
                message="تم تحديث الرمز بنجاح / Token refreshed successfully",
                data=serializer.validated_data
            )

        return unauthorized(
            message="فشل تحديث الرمز / Token refresh failed"
        )


class MeView(APIView):
    """
    GET: Get current authenticated user details
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserDetailSerializer(request.user)
        return success(
            message="تم جلب بياناتك بنجاح / Your data retrieved successfully",
            data=serializer.data
        )


class VerifyTokenView(APIView):
    """
    POST: Verify if access token is valid
    """
    permission_classes = [AllowAny]

    def post(self, request):
        from rest_framework_simplejwt.tokens import AccessToken

        try:
            token = request.data.get('token')

            if not token:
                return bad_request(
                    message="الرمز مطلوب / Token is required"
                )

            # Verify token
            AccessToken(token)

            return success(
                message="الرمز صالح / Token is valid",
                data={"valid": True}
            )

        except TokenError:
            return unauthorized(
                message="الرمز غير صالح أو منتهي الصلاحية / Token is invalid or expired"
            )