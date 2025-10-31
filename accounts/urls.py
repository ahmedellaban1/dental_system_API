"""
=============================================================================
accounts/urls.py - Account Management & JWT Authentication URLs
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PatientViewSet, DoctorViewSet, ReceptionistViewSet,
    MedicalRepViewSet, ProfileViewSet
)
from .auth_views import (
    LoginView, LogoutView, RefreshTokenView,
    MeView, VerifyTokenView
)

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'patients', PatientViewSet, basename='patient')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'receptionists', ReceptionistViewSet, basename='receptionist')
router.register(r'medical-reps', MedicalRepViewSet, basename='medical-rep')
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    # JWT Authentication endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/refresh/', RefreshTokenView.as_view(), name='token-refresh'),
    path('auth/verify/', VerifyTokenView.as_view(), name='token-verify'),
    path('auth/me/', MeView.as_view(), name='me'),

    # User management endpoints
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

AUTHENTICATION (JWT):
---------------------
POST    /api/accounts/auth/login/        - Login (get access + refresh tokens)
POST    /api/accounts/auth/logout/       - Logout (blacklist refresh token)
POST    /api/accounts/auth/refresh/      - Refresh access token
POST    /api/accounts/auth/verify/       - Verify token validity
GET     /api/accounts/auth/me/           - Get current user details

PATIENTS:
---------
GET     /api/accounts/patients/              - List all patients (paginated)
POST    /api/accounts/patients/              - Create new patient (Admin/Receptionist)
GET     /api/accounts/patients/{id}/         - Get patient details
PUT     /api/accounts/patients/{id}/         - Update patient (Admin)
PATCH   /api/accounts/patients/{id}/         - Partial update patient (Admin)
DELETE  /api/accounts/patients/{id}/         - Delete patient (Admin)
POST    /api/accounts/patients/{id}/activate/ - Activate/Deactivate (Admin)

DOCTORS:
--------
GET     /api/accounts/doctors/               - List all doctors (paginated)
POST    /api/accounts/doctors/               - Create new doctor (Admin only)
GET     /api/accounts/doctors/{id}/          - Get doctor details
PUT     /api/accounts/doctors/{id}/          - Update doctor (Admin)
PATCH   /api/accounts/doctors/{id}/          - Partial update doctor (Admin)
DELETE  /api/accounts/doctors/{id}/          - Delete doctor (Admin)
POST    /api/accounts/doctors/{id}/activate/  - Activate/Deactivate (Admin)

RECEPTIONISTS:
--------------
GET     /api/accounts/receptionists/         - List all receptionists (paginated)
POST    /api/accounts/receptionists/         - Create new receptionist (Admin only)
GET     /api/accounts/receptionists/{id}/    - Get receptionist details
PUT     /api/accounts/receptionists/{id}/    - Update receptionist (Admin)
PATCH   /api/accounts/receptionists/{id}/    - Partial update receptionist (Admin)
DELETE  /api/accounts/receptionists/{id}/    - Delete receptionist (Admin)
POST    /api/accounts/receptionists/{id}/activate/ - Activate/Deactivate (Admin)

MEDICAL REPS:
-------------
GET     /api/accounts/medical-reps/          - List all medical reps (paginated)
POST    /api/accounts/medical-reps/          - Create new medical rep (Admin only)
GET     /api/accounts/medical-reps/{id}/     - Get medical rep details
PUT     /api/accounts/medical-reps/{id}/     - Update medical rep (Admin)
PATCH   /api/accounts/medical-reps/{id}/     - Partial update medical rep (Admin)
DELETE  /api/accounts/medical-reps/{id}/     - Delete medical rep (Admin)
POST    /api/accounts/medical-reps/{id}/activate/ - Activate/Deactivate (Admin)

PROFILES:
---------
GET     /api/accounts/profiles/              - List profiles (own or all for staff)
GET     /api/accounts/profiles/{user_id}/    - Get specific profile
PUT     /api/accounts/profiles/{user_id}/    - Update profile (owner/staff)
PATCH   /api/accounts/profiles/{user_id}/    - Partial update profile (owner/staff)
GET     /api/accounts/profiles/me/           - Get current user's profile
POST    /api/accounts/profiles/change_password/ - Change password

=============================================================================
Example Requests with JWT:
=============================================================================

1. LOGIN:
---------
POST /api/accounts/auth/login/
{
    "username": "patient123",
    "password": "SecurePass123!"
}

RESPONSE:
{
    "status": "success",
    "message": "مرحباً أحمد! تم تسجيل الدخول بنجاح / Welcome! Login successful",
    "data": {
        "id": 1,
        "username": "patient123",
        "email": "patient@example.com",
        "first_name": "أحمد",
        "last_name": "محمد",
        "type": "patient",
        "is_active": true,
        "date_joined": "2025-10-31T10:30:00Z",
        "profile": {
            "image": "/media/Profile/10-2025/1234567890.jpg",
            "city_details": {
                "id": 1,
                "name": "Cairo",
                "country": "Egypt",
                "region": "Cairo Governorate"
            },
            "address": "123 شارع الجامعة",
            "phone": "01012345678",
            "date_of_birth": "1990-05-15",
            "age": 35,
            "gender": "male"
        },
        "tokens": {
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }
    }
}

2. REFRESH TOKEN:
-----------------
POST /api/accounts/auth/refresh/
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

RESPONSE:
{
    "status": "success",
    "message": "تم تحديث الرمز بنجاح / Token refreshed successfully",
    "data": {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}

3. VERIFY TOKEN:
----------------
POST /api/accounts/auth/verify/
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

RESPONSE:
{
    "status": "success",
    "message": "الرمز صالح / Token is valid",
    "data": {
        "valid": true
    }
}

4. GET CURRENT USER:
--------------------
GET /api/accounts/auth/me/
Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

RESPONSE:
{
    "status": "success",
    "message": "تم جلب بياناتك بنجاح / Your data retrieved successfully",
    "data": {
        "id": 1,
        "username": "patient123",
        "email": "patient@example.com",
        "first_name": "أحمد",
        "last_name": "محمد",
        "type": "patient",
        "is_active": true,
        "date_joined": "2025-10-31T10:30:00Z",
        "last_login": "2025-10-31T12:00:00Z",
        "profile": { ... }
    }
}

5. LOGOUT:
----------
POST /api/accounts/auth/logout/
Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
{
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

RESPONSE:
{
    "status": "success",
    "message": "تم تسجيل الخروج بنجاح / Logout successful",
    "data": null
}

6. CREATE PATIENT (with token response):
-----------------------------------------
POST /api/accounts/patients/
Headers: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
{
    "username": "patient123",
    "email": "patient@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!",
    "first_name": "أحمد",
    "last_name": "محمد",
    "phone": "01012345678",
    "address": "123 شارع الجامعة، القاهرة",
    "date_of_birth": "1990-05-15",
    "gender": "male",
    "city": 1
}

RESPONSE:
{
    "status": "success",
    "message": "تم إنشاء حساب المريض بنجاح / Patient account created successfully",
    "data": {
        "id": 1,
        "username": "patient123",
        "email": "patient@example.com",
        "first_name": "أحمد",
        "last_name": "محمد",
        "type": "patient",
        "is_active": false,
        "date_joined": "2025-10-31T10:30:00Z",
        "last_login": null,
        "profile": { ... }
    }
}

7. AUTHENTICATED REQUESTS:
---------------------------
Always include JWT token in Authorization header:
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

GET /api/accounts/patients/
GET /api/accounts/doctors/5/
PATCH /api/accounts/profiles/3/
POST /api/accounts/profiles/change_password/

=============================================================================
JWT Configuration (add to settings.py):
=============================================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# Add to INSTALLED_APPS:
INSTALLED_APPS = [
    ...
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # For logout
    ...
]

# Add to REST_FRAMEWORK:
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

=============================================================================
"""