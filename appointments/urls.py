"""
=============================================================================
appointments/urls.py - Appointment Booking URLs
=============================================================================
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

BOOKINGS - CRUD Operations:
---------------------------
GET     /api/appointments/bookings/              - List bookings (filtered by role)
POST    /api/appointments/bookings/              - Create new booking
GET     /api/appointments/bookings/{id}/         - Get booking details
PUT     /api/appointments/bookings/{id}/         - Update booking (full)
PATCH   /api/appointments/bookings/{id}/         - Update booking (partial)
DELETE  /api/appointments/bookings/{id}/         - Delete booking (Admin only)

BOOKINGS - Status Management:
-----------------------------
POST    /api/appointments/bookings/{id}/cancel/   - Cancel booking
POST    /api/appointments/bookings/{id}/confirm/  - Confirm booking (Staff only)
POST    /api/appointments/bookings/{id}/complete/ - Mark as completed (Staff only)

BOOKINGS - Filtering & Views:
-----------------------------
GET     /api/appointments/bookings/my_bookings/  - Get current user's bookings
GET     /api/appointments/bookings/today/        - Get today's bookings
GET     /api/appointments/bookings/upcoming/     - Get upcoming bookings (7 days)
GET     /api/appointments/bookings/past/         - Get past bookings
GET     /api/appointments/bookings/by_doctor/    - Get bookings by doctor (Staff)
GET     /api/appointments/bookings/by_patient/   - Get bookings by patient (Staff)

BOOKINGS - Statistics & Availability:
-------------------------------------
GET     /api/appointments/bookings/statistics/   - Get booking statistics (Staff)
GET     /api/appointments/bookings/available_slots/ - Get available time slots

=============================================================================
Query Parameters:
=============================================================================

Filtering:
----------
?status=pending                - Filter by status (pending/confirmed/completed/cancelled)
?doctor=1                      - Filter by doctor ID
?patient=2                     - Filter by patient ID
?appointment_datetime=2025-11-01 - Filter by date

Search:
-------
?search=ahmed                  - Search in patient/doctor names, reason

Ordering:
---------
?ordering=-appointment_datetime - Order by appointment date (desc)
?ordering=status                - Order by status (asc)
?ordering=created_at            - Order by creation date

Pagination:
-----------
?page=2                        - Page number
?page_size=10                  - Items per page (max 20)

=============================================================================
Example Requests:
=============================================================================

1. CREATE BOOKING (Patient - Self):
------------------------------------
POST /api/appointments/bookings/
Headers: Authorization: Bearer <token>
{
    "doctor": 5,
    "appointment_datetime": "2025-11-15 10:00:00",
    "reason": "تنظيف أسنان / Teeth cleaning"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إنشاء الحجز بنجاح / Booking created successfully",
    "data": {
        "id": 1,
        "patient": 3,
        "patient_details": {
            "id": 3,
            "username": "patient123",
            "full_name": "أحمد محمد",
            "email": "patient@example.com",
            "phone": "01012345678"
        },
        "doctor": 5,
        "doctor_details": {
            "id": 5,
            "username": "dr_ahmed",
            "full_name": "د. أحمد السيد",
            "email": "ahmed@clinic.com",
            "phone": "01098765432"
        },
        "appointment_datetime": "2025-11-15T10:00:00Z",
        "status": "pending",
        "status_display": "قيد الانتظار",
        "reason": "تنظيف أسنان / Teeth cleaning",
        "notes": "",
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

2. CREATE BOOKING (Receptionist - Any Patient):
------------------------------------------------
POST /api/appointments/bookings/
Headers: Authorization: Bearer <token>
{
    "patient": 3,
    "doctor": 5,
    "appointment_datetime": "2025-11-15 14:30:00",
    "reason": "فحص دوري / Regular checkup",
    "notes": "مريض جديد / New patient"
}

3. GET AVAILABLE SLOTS:
-----------------------
GET /api/appointments/bookings/available_slots/?doctor=5&date=2025-11-15

RESPONSE:
{
    "status": "success",
    "message": "المواعيد المتاحة في 2025-11-15 / Available slots on 2025-11-15",
    "data": {
        "available_slots": [
            "2025-11-15 08:00:00",
            "2025-11-15 08:30:00",
            "2025-11-15 09:00:00",
            "2025-11-15 09:30:00",
            "2025-11-15 11:00:00",
            "2025-11-15 11:30:00",
            ...
        ],
        "count": 20
    }
}

4. CONFIRM BOOKING (Staff):
----------------------------
POST /api/appointments/bookings/1/confirm/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "تم تأكيد الحجز بنجاح / Booking confirmed successfully",
    "data": { ... }
}

5. CANCEL BOOKING:
------------------
POST /api/appointments/bookings/1/cancel/
Headers: Authorization: Bearer <token>
{
    "reason": "طارئ / Emergency"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إلغاء الحجز بنجاح / Booking cancelled successfully",
    "data": { ... }
}

6. GET TODAY'S BOOKINGS:
------------------------
GET /api/appointments/bookings/today/

RESPONSE:
{
    "status": "success",
    "message": "حجوزات اليوم (2025-10-31) / Today's bookings (2025-10-31)",
    "data": [
        {
            "id": 1,
            "patient": 3,
            "patient_name": "أحمد محمد",
            "doctor": 5,
            "doctor_name": "د. أحمد السيد",
            "appointment_datetime": "2025-10-31T10:00:00Z",
            "status": "confirmed",
            "status_display": "مؤكد",
            "created_at": "2025-10-30T12:00:00Z"
        },
        ...
    ]
}

7. GET UPCOMING BOOKINGS (Next 7 Days):
----------------------------------------
GET /api/appointments/bookings/upcoming/

8. GET MY BOOKINGS:
-------------------
GET /api/appointments/bookings/my_bookings/

9. GET BOOKING STATISTICS (Staff):
-----------------------------------
GET /api/appointments/bookings/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات الحجوزات / Booking statistics",
    "data": {
        "total_bookings": 150,
        "pending_bookings": 25,
        "confirmed_bookings": 50,
        "completed_bookings": 60,
        "cancelled_bookings": 15,
        "today_bookings": 8,
        "upcoming_bookings": 30
    }
}

10. GET DOCTOR'S BOOKINGS (Staff):
-----------------------------------
GET /api/appointments/bookings/by_doctor/?doctor=5

11. GET PATIENT'S BOOKINGS (Staff):
------------------------------------
GET /api/appointments/bookings/by_patient/?patient=3

12. UPDATE BOOKING (Patient - Reason only for pending):
--------------------------------------------------------
PATCH /api/appointments/bookings/1/
Headers: Authorization: Bearer <token>
{
    "reason": "سبب محدث / Updated reason"
}

13. UPDATE BOOKING (Doctor - Status and notes):
------------------------------------------------
PATCH /api/appointments/bookings/1/
Headers: Authorization: Bearer <token>
{
    "status": "completed",
    "notes": "تم الفحص بنجاح / Examination completed successfully"
}

14. UPDATE BOOKING (Staff - All fields):
-----------------------------------------
PATCH /api/appointments/bookings/1/
Headers: Authorization: Bearer <token>
{
    "appointment_datetime": "2025-11-15 11:00:00",
    "status": "confirmed",
    "notes": "تم تغيير الموعد / Appointment rescheduled"
}

15. COMPLETE BOOKING (Staff):
------------------------------
POST /api/appointments/bookings/1/complete/

16. GET FILTERED BOOKINGS:
---------------------------
GET /api/appointments/bookings/?status=confirmed&doctor=5&ordering=-appointment_datetime

=============================================================================
Business Rules:
=============================================================================

1. BOOKING CREATION:
   - Patients can only book for themselves
   - Staff (Admin/Receptionist) can book for any patient
   - One booking per patient per day
   - Appointments must be in the future
   - Working hours: 8 AM - 8 PM
   - No bookings on Fridays
   - 30-minute time slots
   - Doctor must be available (no conflicting bookings)

2. BOOKING UPDATES:
   - Patients: Can only update reason for pending bookings
   - Doctors: Can update status and notes for their bookings
   - Staff: Can update all fields for any booking
   - Cannot modify cancelled or completed bookings

3. BOOKING CANCELLATION:
   - Patients: Can cancel their own pending/confirmed bookings
   - Doctors: Can cancel their bookings
   - Staff: Can cancel any booking
   - Cannot cancel completed bookings

4. BOOKING CONFIRMATION:
   - Only staff can confirm pending bookings

5. BOOKING COMPLETION:
   - Only staff can mark bookings as completed
   - Cannot complete cancelled bookings

6. VIEW PERMISSIONS:
   - Patients: See only their bookings
   - Doctors: See only their bookings
   - Staff: See all bookings

=============================================================================
Validation Rules:
=============================================================================

1. Patient must be active and have type='patient'
2. Doctor must be active and have type='doctor'
3. Appointment must be:
   - In the future
   - During working hours (8 AM - 8 PM)
   - Not on Friday
   - On an available time slot (no conflicts)
4. Only one booking per patient per day
5. Status transitions:
   - pending → confirmed/cancelled
   - confirmed → completed/cancelled
   - completed → no changes
   - cancelled → no changes

=============================================================================
"""