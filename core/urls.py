"""
=============================================================================
core/urls.py - Main Project URL Configuration
Dental System API
=============================================================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # ======================== Admin Panel ========================
    path('admin/', admin.site.urls),

    # ======================== API Documentation ========================
    # Schema generation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI - Interactive API documentation
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # ReDoc - Alternative API documentation
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ======================== API Endpoints ========================
    # Accounts & Authentication
    path('api/accounts/', include('accounts.urls')),

    # Appointments
    path('api/appointments/', include('appointments.urls')),
    #
    # # Medical Records
    # path('api/medical/', include('medical.urls')),
    #
    # # Operations
    # path('api/operations/', include('operations.urls')),
    #
    # # Billing & Invoices
    # path('api/billing/', include('billing.urls')),
    #
    # # Payroll & Salaries
    # path('api/payroll/', include('payroll.urls')),
    #
    # # Pharmacy & Medicines
    # path('api/pharmacy/', include('pharmacy.urls')),
]

# ======================== Debug Toolbar (Development Only) ========================
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# ======================== Media & Static Files (Development Only) ========================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ======================== Admin Customization ========================
admin.site.site_header = "نظام إدارة عيادة الاسنان / Dental Clinic Management"
admin.site.site_title = "إدارة العيادة / Clinic Admin"
admin.site.index_title = "لوحة التحكم / Dashboard"

"""
=============================================================================
API STRUCTURE OVERVIEW
=============================================================================

BASE URL: http://localhost:8000/api/

AUTHENTICATION & ACCOUNTS:
--------------------------
POST   /api/accounts/auth/login/              - Login (JWT)
POST   /api/accounts/auth/logout/             - Logout
POST   /api/accounts/auth/refresh/            - Refresh token
POST   /api/accounts/auth/verify/             - Verify token
GET    /api/accounts/auth/me/                 - Current user

GET    /api/accounts/patients/                - List patients
POST   /api/accounts/patients/                - Create patient
GET    /api/accounts/patients/{id}/           - Patient details
PATCH  /api/accounts/patients/{id}/           - Update patient
DELETE /api/accounts/patients/{id}/           - Delete patient

GET    /api/accounts/doctors/                 - List doctors
POST   /api/accounts/doctors/                 - Create doctor (admin)
GET    /api/accounts/doctors/{id}/            - Doctor details
PATCH  /api/accounts/doctors/{id}/            - Update doctor

GET    /api/accounts/receptionists/           - List receptionists
GET    /api/accounts/medical-reps/            - List medical reps

GET    /api/accounts/profiles/                - List profiles
GET    /api/accounts/profiles/me/             - My profile
PATCH  /api/accounts/profiles/{id}/           - Update profile
POST   /api/accounts/profiles/change_password/ - Change password

APPOINTMENTS:
-------------
GET    /api/appointments/                     - List appointments
POST   /api/appointments/                     - Create appointment
GET    /api/appointments/{id}/                - Appointment details
PATCH  /api/appointments/{id}/                - Update appointment
DELETE /api/appointments/{id}/                - Cancel appointment

MEDICAL RECORDS:
----------------
GET    /api/medical/records/                  - List medical records
POST   /api/medical/records/                  - Create record
GET    /api/medical/records/{id}/             - Record details
PATCH  /api/medical/records/{id}/             - Update record

GET    /api/medical/diseases/                 - List diseases
GET    /api/medical/prescriptions/            - List prescriptions
GET    /api/medical/diagnoses/                - List diagnoses

OPERATIONS:
-----------
GET    /api/operations/                       - List operations
POST   /api/operations/                       - Create operation
GET    /api/operations/{id}/                  - Operation details
PATCH  /api/operations/{id}/                  - Update operation

GET    /api/operations/media/                 - Operation media
POST   /api/operations/media/                 - Upload media

BILLING:
--------
GET    /api/billing/invoices/                 - List invoices
POST   /api/billing/invoices/                 - Create invoice
GET    /api/billing/invoices/{id}/            - Invoice details
PATCH  /api/billing/invoices/{id}/            - Update invoice

GET    /api/billing/payments/                 - List payments
POST   /api/billing/payments/                 - Record payment

PAYROLL:
--------
GET    /api/payroll/salaries/                 - List salaries
POST   /api/payroll/salaries/                 - Create salary
GET    /api/payroll/salaries/{id}/            - Salary details
PATCH  /api/payroll/salaries/{id}/            - Update salary

GET    /api/payroll/advances/                 - List advances
POST   /api/payroll/advances/                 - Request advance

PHARMACY:
---------
GET    /api/pharmacy/medicines/               - List medicines
POST   /api/pharmacy/medicines/               - Add medicine
GET    /api/pharmacy/medicines/{id}/          - Medicine details
PATCH  /api/pharmacy/medicines/{id}/          - Update medicine

GET    /api/pharmacy/inventory/               - Check inventory
GET    /api/pharmacy/low-stock/               - Low stock items

=============================================================================
API DOCUMENTATION
=============================================================================

Interactive Documentation (Swagger):
http://localhost:8000/api/docs/

Alternative Documentation (ReDoc):
http://localhost:8000/api/redoc/

API Schema (JSON):
http://localhost:8000/api/schema/

=============================================================================
ADMIN PANEL
=============================================================================

Django Admin:
http://localhost:8000/admin/

Debug Toolbar (Development):
Available on all pages when DEBUG=True

=============================================================================
"""