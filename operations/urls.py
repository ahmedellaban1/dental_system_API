"""
=============================================================================
operations/urls.py - Operations & Media Management URLs
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OperationViewSet, OperationMediaViewSet

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'operations', OperationViewSet, basename='operation')
router.register(r'media', OperationMediaViewSet, basename='operation-media')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

OPERATIONS - CRUD:
------------------
GET     /api/operations/operations/              - List operations (filtered by role)
POST    /api/operations/operations/              - Create operation (Doctor/Admin)
GET     /api/operations/operations/{id}/         - Get operation details
PUT     /api/operations/operations/{id}/         - Update operation (Doctor/Admin)
PATCH   /api/operations/operations/{id}/         - Partial update (Doctor/Admin)
DELETE  /api/operations/operations/{id}/         - Delete operation (Admin)

OPERATIONS - Status Management:
-------------------------------
POST    /api/operations/operations/{id}/update_status/ - Update status
POST    /api/operations/operations/{id}/complete/      - Mark as completed
POST    /api/operations/operations/{id}/cancel/        - Cancel operation

OPERATIONS - Filtering & Views:
-------------------------------
GET     /api/operations/operations/my_operations/ - Current user's operations
GET     /api/operations/operations/scheduled/     - Scheduled operations
GET     /api/operations/operations/completed/     - Completed operations
GET     /api/operations/operations/today/         - Today's operations
GET     /api/operations/operations/by_doctor/     - Operations by doctor (Staff)
GET     /api/operations/operations/by_patient/    - Operations by patient (Staff)

OPERATIONS - Statistics:
------------------------
GET     /api/operations/operations/statistics/        - Overall statistics (Staff)
GET     /api/operations/operations/doctor_statistics/ - Stats by doctor (Staff)
GET     /api/operations/operations/operation_types/   - Stats by type (Staff)

MEDIA - CRUD:
-------------
GET     /api/operations/media/                   - List media files
POST    /api/operations/media/                   - Upload media (Doctor/Admin)
GET     /api/operations/media/{id}/              - Get media details
DELETE  /api/operations/media/{id}/              - Delete media (Doctor/Admin)

MEDIA - Filtering:
------------------
GET     /api/operations/media/by_operation/      - Media by operation ID
GET     /api/operations/media/by_type/           - Media by type

=============================================================================
Query Parameters:
=============================================================================

Operations:
-----------
?status=scheduled              - Filter by status
?doctor=1                      - Filter by doctor ID
?patient=2                     - Filter by patient ID
?operation_date=2025-11-01     - Filter by date
?search=cleaning               - Search in operation name, description

Media:
------
?operation=5                   - Filter by operation ID
?media_type=xray               - Filter by media type
?search=description            - Search in description

Ordering:
---------
?ordering=-operation_date      - Order by operation date (desc)
?ordering=cost                 - Order by cost (asc)
?ordering=-created_at          - Order by creation date (desc)

Pagination:
-----------
?page=2                        - Page number
?page_size=10                  - Items per page (max 20)

=============================================================================
Example Requests:
=============================================================================

1. CREATE OPERATION (Doctor/Admin):
------------------------------------
POST /api/operations/operations/
Headers: Authorization: Bearer <token>
{
    "patient": 3,
    "doctor": 5,
    "booking": 10,
    "operation_name": "تنظيف أسنان شامل / Deep Teeth Cleaning",
    "description": "تنظيف عميق لإزالة الجير والبلاك",
    "procedure_details": "استخدام أدوات الموجات فوق الصوتية",
    "cost": 1500.00,
    "operation_date": "2025-11-15",
    "duration": "01:30:00",
    "status": "scheduled",
    "notes": "المريض يعاني من حساسية الأسنان"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إنشاء العملية بنجاح / Operation created successfully",
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
            "full_name": "د. أحمد السيد"
        },
        "booking": 10,
        "booking_details": {
            "id": 10,
            "appointment_datetime": "2025-11-15T10:00:00Z",
            "status": "confirmed"
        },
        "operation_name": "تنظيف أسنان شامل / Deep Teeth Cleaning",
        "description": "تنظيف عميق لإزالة الجير والبلاك",
        "procedure_details": "استخدام أدوات الموجات فوق الصوتية",
        "cost": 1500.00,
        "operation_date": "2025-11-15",
        "duration": "01:30:00",
        "duration_display": "01:30",
        "status": "scheduled",
        "status_display": "مجدول",
        "notes": "المريض يعاني من حساسية الأسنان",
        "media_files": [],
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

2. UPLOAD OPERATION MEDIA (Doctor/Admin):
------------------------------------------
POST /api/operations/media/
Headers: 
  Authorization: Bearer <token>
  Content-Type: multipart/form-data
Form Data:
  operation: 1
  media_type: xray
  file_path: [binary file]
  description: صورة أشعة قبل العملية / X-ray before operation

RESPONSE:
{
    "status": "success",
    "message": "تم رفع الملف بنجاح / File uploaded successfully",
    "data": {
        "id": 1,
        "operation": 1,
        "media_type": "xray",
        "media_type_display": "أشعة",
        "file_url": "http://localhost:8000/media/Product/Xray/10-2025/123456789012345.jpg",
        "file_name": "123456789012345.jpg",
        "file_size": 2.45,
        "description": "صورة أشعة قبل العملية / X-ray before operation",
        "created_at": "2025-10-31T12:30:00Z"
    }
}

3. COMPLETE OPERATION:
----------------------
POST /api/operations/operations/1/complete/

RESPONSE:
{
    "status": "success",
    "message": "تم تحديث حالة العملية إلى مكتمل / Operation marked as completed",
    "data": { ... }
}

4. UPDATE OPERATION STATUS:
----------------------------
POST /api/operations/operations/1/update_status/
{
    "status": "in_progress",
    "notes": "بدأت العملية في الموعد المحدد"
}

5. GET MY OPERATIONS (Patient or Doctor):
------------------------------------------
GET /api/operations/operations/my_operations/

RESPONSE:
{
    "status": "success",
    "message": "عملياتك / Your operations",
    "data": [
        {
            "id": 1,
            "patient": 3,
            "patient_name": "أحمد محمد",
            "doctor": 5,
            "doctor_name": "د. أحمد السيد",
            "operation_name": "تنظيف أسنان شامل",
            "cost": 1500.00,
            "operation_date": "2025-11-15",
            "status": "scheduled",
            "status_display": "مجدول",
            "media_count": 2,
            "created_at": "2025-10-31T12:00:00Z"
        },
        ...
    ]
}

6. GET TODAY'S OPERATIONS:
--------------------------
GET /api/operations/operations/today/

7. GET OPERATION STATISTICS (Staff):
-------------------------------------
GET /api/operations/operations/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات العمليات / Operation statistics",
    "data": {
        "total_operations": 250,
        "scheduled_operations": 45,
        "in_progress_operations": 5,
        "completed_operations": 180,
        "cancelled_operations": 20,
        "total_revenue": 375000.00,
        "today_operations": 8,
        "this_month_operations": 65
    }
}

8. GET DOCTOR STATISTICS (Staff):
----------------------------------
GET /api/operations/operations/doctor_statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات الأطباء / Doctor statistics",
    "data": [
        {
            "doctor_id": 5,
            "doctor_name": "د. أحمد السيد",
            "total_operations": 85,
            "completed_operations": 75,
            "total_revenue": 125000.00
        },
        ...
    ]
}

9. GET OPERATION TYPES STATISTICS (Staff):
-------------------------------------------
GET /api/operations/operations/operation_types/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات أنواع العمليات / Operation type statistics",
    "data": [
        {
            "operation_name": "تنظيف أسنان",
            "count": 120,
            "total_revenue": 180000.00,
            "avg_cost": 1500.00
        },
        {
            "operation_name": "حشو أسنان",
            "count": 85,
            "total_revenue": 127500.00,
            "avg_cost": 1500.00
        },
        ...
    ]
}

10. GET OPERATION MEDIA:
------------------------
GET /api/operations/media/by_operation/?operation=1

RESPONSE:
{
    "status": "success",
    "message": "ملفات العملية / Operation media files",
    "data": [
        {
            "id": 1,
            "operation": 1,
            "media_type": "xray",
            "media_type_display": "أشعة",
            "file_url": "http://localhost:8000/media/...",
            "file_name": "xray_001.jpg",
            "description": "صورة أشعة قبل العملية",
            "created_at": "2025-10-31T12:30:00Z"
        },
        ...
    ]
}

11. GET MEDIA BY TYPE:
----------------------
GET /api/operations/media/by_type/?type=xray

12. DELETE MEDIA FILE:
----------------------
DELETE /api/operations/media/1/

13. CANCEL OPERATION:
---------------------
POST /api/operations/operations/1/cancel/

14. GET PATIENT'S OPERATIONS (Staff):
--------------------------------------
GET /api/operations/operations/by_patient/?patient=3

15. GET DOCTOR'S OPERATIONS (Staff):
-------------------------------------
GET /api/operations/operations/by_doctor/?doctor=5

16. FILTER OPERATIONS:
----------------------
GET /api/operations/operations/?status=completed&doctor=5&ordering=-operation_date

=============================================================================
Business Rules:
=============================================================================

1. OPERATION CREATION:
   - Only Doctors and Admin can create operations
   - Patient must be active with type='patient'
   - Doctor must be active with type='doctor'
   - Cost must be non-negative
   - Booking (optional) must belong to patient
   - Booking can only be linked to one operation (OneToOne)

2. OPERATION UPDATES:
   - Cannot change patient or doctor after creation
   - Can update: name, description, procedure_details, cost, date, duration, status, notes
   - Status transitions:
     * scheduled → in_progress → completed
     * scheduled → cancelled
     * in_progress → cancelled
     * Cannot modify completed/cancelled operations

3. OPERATION DELETION:
   - Only Admin can delete
   - Cannot delete if operation has bills

4. MEDIA MANAGEMENT:
   - Only Doctors (own operations) and Admin can upload
   - Supported types: image, video, audio, document, xray, other
   - Max file size: 5MB
   - Files stored in: media/Product/{Type}/{MM-YYYY}/
   - Deleting media also deletes file from storage

5. VIEW PERMISSIONS:
   - Patients: See only their operations
   - Doctors: See only their operations
   - Staff: See all operations

6. STATUS WORKFLOW:
   scheduled (مجدول)
      ↓
   in_progress (جاري التنفيذ)
      ↓
   completed (مكتمل)

   Any status → cancelled (ملغي) (except completed)

=============================================================================
Media Types:
=============================================================================

image (صورة):
- General images, photos
- Formats: JPG, PNG, GIF

video (فيديو):
- Procedure recordings
- Formats: MP4, AVI

audio (صوت):
- Voice notes, recordings
- Formats: MP3, WAV

document (مستند):
- Reports, documents
- Formats: PDF, DOC, DOCX

xray (أشعة):
- X-ray images
- Formats: JPG, PNG, DICOM

other (أخرى):
- Other file types

=============================================================================
Integration with Other Apps:
=============================================================================

1. APPOINTMENTS:
   - Operation can link to Booking (optional)
   - OneToOne relationship (one booking = one operation max)

2. BILLING:
   - Bill references Operation for cost
   - Bill.total_amount = Operation.cost
   - Cannot delete operation with bills

3. ACCOUNTS:
   - Patient and Doctor from CustomUser
   - Type validation enforced

=============================================================================
"""