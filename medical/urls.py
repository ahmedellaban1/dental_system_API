"""
=============================================================================
medical/urls.py - Medical Records & Diseases Management URLs
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommonDiseaseViewSet, ChronicDiseaseViewSet

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'diseases', CommonDiseaseViewSet, basename='disease')
router.register(r'chronic', ChronicDiseaseViewSet, basename='chronic-disease')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

COMMON DISEASES (Library):
---------------------------
GET     /api/medical/diseases/                - List all diseases
POST    /api/medical/diseases/                - Add new disease (Admin/Doctor)
GET     /api/medical/diseases/{id}/           - Get disease details
PUT     /api/medical/diseases/{id}/           - Update disease (Admin/Doctor)
PATCH   /api/medical/diseases/{id}/           - Partial update (Admin/Doctor)
DELETE  /api/medical/diseases/{id}/           - Delete disease (Admin/Doctor)

COMMON DISEASES - Filtering & Views:
-------------------------------------
GET     /api/medical/diseases/by_category/    - Get diseases by category
GET     /api/medical/diseases/statistics/     - Disease library statistics (Staff)
GET     /api/medical/diseases/{id}/patients/  - Get patients with this disease

CHRONIC DISEASES (Patient Records):
------------------------------------
GET     /api/medical/chronic/                 - List chronic disease records
POST    /api/medical/chronic/                 - Add chronic disease (Doctor/Staff)
GET     /api/medical/chronic/{id}/            - Get record details
PUT     /api/medical/chronic/{id}/            - Update record (Doctor/Staff)
PATCH   /api/medical/chronic/{id}/            - Partial update (Doctor/Staff)
DELETE  /api/medical/chronic/{id}/            - Delete record (Admin)

CHRONIC DISEASES - Status Management:
--------------------------------------
POST    /api/medical/chronic/{id}/activate/   - Mark disease as active
POST    /api/medical/chronic/{id}/deactivate/ - Mark disease as inactive

CHRONIC DISEASES - Filtering & Views:
--------------------------------------
GET     /api/medical/chronic/my_diseases/     - Get current patient's diseases
GET     /api/medical/chronic/active/          - Get active chronic diseases
GET     /api/medical/chronic/inactive/        - Get inactive chronic diseases
GET     /api/medical/chronic/by_patient/      - Get diseases by patient (Staff)

CHRONIC DISEASES - Statistics & Reports:
-----------------------------------------
GET     /api/medical/chronic/patient_summary/ - Patient medical summary (Staff)
GET     /api/medical/chronic/overview/        - Medical system overview (Staff)
GET     /api/medical/chronic/category_statistics/ - Stats by category (Staff)

=============================================================================
Query Parameters:
=============================================================================

Common Diseases:
----------------
?category=chronic              - Filter by category
?search=diabetes               - Search in disease names, symptoms

Chronic Diseases:
-----------------
?patient=1                     - Filter by patient ID
?disease=5                     - Filter by disease ID
?disease__category=chronic     - Filter by disease category
?is_active=true                - Filter by active status
?search=ahmed                  - Search in patient name, disease name

Ordering:
---------
?ordering=disease_name_ar      - Order by Arabic name (asc)
?ordering=-diagnosed_date      - Order by diagnosis date (desc)
?ordering=created_at           - Order by creation date

Pagination:
-----------
?page=2                        - Page number
?page_size=10                  - Items per page (max 20)

=============================================================================
Example Requests:
=============================================================================

1. ADD DISEASE TO LIBRARY (Doctor/Admin):
------------------------------------------
POST /api/medical/diseases/
Headers: Authorization: Bearer <token>
{
    "disease_name_ar": "السكري",
    "disease_name_en": "Diabetes",
    "description": "مرض مزمن يؤثر على مستوى السكر في الدم",
    "category": "chronic",
    "symptoms": "عطش شديد، كثرة التبول، تعب، فقدان الوزن",
    "common_treatments": "الأنسولين، تنظيم النظام الغذائي، ممارسة الرياضة"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إضافة المرض بنجاح / Disease added successfully",
    "data": {
        "id": 1,
        "disease_name_ar": "السكري",
        "disease_name_en": "Diabetes",
        "description": "مرض مزمن يؤثر على مستوى السكر في الدم",
        "category": "chronic",
        "category_display": "مزمن",
        "symptoms": "عطش شديد، كثرة التبول، تعب، فقدان الوزن",
        "common_treatments": "الأنسولين، تنظيم النظام الغذائي، ممارسة الرياضة",
        "patient_count": 0,
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

2. ADD CHRONIC DISEASE TO PATIENT (Doctor/Staff):
--------------------------------------------------
POST /api/medical/chronic/
Headers: Authorization: Bearer <token>
{
    "patient": 3,
    "disease": 1,
    "description": "مرض السكري من النوع الثاني",
    "diagnosed_date": "2024-05-15",
    "is_active": true
}

RESPONSE:
{
    "status": "success",
    "message": "تم إضافة السجل الطبي بنجاح / Medical record added successfully",
    "data": {
        "id": 1,
        "patient": 3,
        "patient_details": {
            "id": 3,
            "username": "patient123",
            "full_name": "أحمد محمد",
            "email": "patient@example.com",
            "phone": "01012345678",
            "date_of_birth": "1980-05-15"
        },
        "disease": 1,
        "disease_details": {
            "id": 1,
            "disease_name_ar": "السكري",
            "disease_name_en": "Diabetes",
            "category": "chronic",
            "category_display": "مزمن",
            ...
        },
        "description": "مرض السكري من النوع الثاني",
        "diagnosed_date": "2024-05-15",
        "is_active": true,
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

3. GET MY CHRONIC DISEASES (Patient):
--------------------------------------
GET /api/medical/chronic/my_diseases/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "سجلاتك الطبية / Your medical records",
    "data": [
        {
            "id": 1,
            "patient": 3,
            "patient_name": "أحمد محمد",
            "disease": 1,
            "disease_name_ar": "السكري",
            "disease_name_en": "Diabetes",
            "disease_category": "مزمن",
            "diagnosed_date": "2024-05-15",
            "is_active": true,
            "created_at": "2025-10-31T12:00:00Z"
        },
        ...
    ]
}

4. DEACTIVATE CHRONIC DISEASE (Doctor/Staff):
----------------------------------------------
POST /api/medical/chronic/1/deactivate/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "تم تعطيل السجل بنجاح / Record deactivated successfully",
    "data": { ... }
}

5. GET PATIENT MEDICAL SUMMARY (Staff):
----------------------------------------
GET /api/medical/chronic/patient_summary/?patient=3

RESPONSE:
{
    "status": "success",
    "message": "ملخص طبي لـ أحمد محمد / Medical summary for Ahmed Mohamed",
    "data": {
        "patient_id": 3,
        "patient_name": "أحمد محمد",
        "total_chronic_diseases": 3,
        "active_diseases": 2,
        "inactive_diseases": 1,
        "chronic_count": 2,
        "infectious_count": 0,
        "genetic_count": 1,
        "other_count": 0
    }
}

6. GET DISEASE LIBRARY STATISTICS (Staff):
-------------------------------------------
GET /api/medical/diseases/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات مكتبة الأمراض / Disease library statistics",
    "data": {
        "total_diseases": 150,
        "by_category": {
            "مزمن": 45,
            "معدي": 30,
            "وراثي": 25,
            "أخرى": 50
        },
        "most_common": [
            {
                "id": 1,
                "name_ar": "السكري",
                "name_en": "Diabetes",
                "patient_count": 25
            },
            {
                "id": 2,
                "name_ar": "ارتفاع ضغط الدم",
                "name_en": "Hypertension",
                "patient_count": 20
            },
            ...
        ]
    }
}

7. GET MEDICAL SYSTEM OVERVIEW (Staff):
----------------------------------------
GET /api/medical/chronic/overview/

RESPONSE:
{
    "status": "success",
    "message": "نظرة عامة على النظام الطبي / Medical system overview",
    "data": {
        "total_patients_with_chronic": 75,
        "total_chronic_disease_records": 150,
        "total_active_diseases": 120,
        "total_disease_library": 150,
        "category_breakdown": {
            "مزمن": 60,
            "معدي": 25,
            "وراثي": 20,
            "أخرى": 15
        }
    }
}

8. GET PATIENTS WITH SPECIFIC DISEASE:
---------------------------------------
GET /api/medical/diseases/1/patients/

RESPONSE:
{
    "status": "success",
    "message": "المرضى المصابون بـ السكري / Patients with Diabetes",
    "data": [
        {
            "id": 1,
            "patient": 3,
            "patient_name": "أحمد محمد",
            "disease": 1,
            "disease_name_ar": "السكري",
            "disease_name_en": "Diabetes",
            "diagnosed_date": "2024-05-15",
            "is_active": true
        },
        ...
    ]
}

9. GET DISEASES BY CATEGORY:
-----------------------------
GET /api/medical/diseases/by_category/?category=chronic

10. GET CATEGORY STATISTICS (Staff):
-------------------------------------
GET /api/medical/chronic/category_statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات حسب فئة المرض / Statistics by disease category",
    "data": [
        {
            "category": "chronic",
            "category_display": "مزمن",
            "disease_count": 45,
            "patient_count": 60
        },
        {
            "category": "infectious",
            "category_display": "معدي",
            "disease_count": 30,
            "patient_count": 25
        },
        ...
    ]
}

11. GET ACTIVE CHRONIC DISEASES:
---------------------------------
GET /api/medical/chronic/active/

12. UPDATE CHRONIC DISEASE (Doctor/Staff):
-------------------------------------------
PATCH /api/medical/chronic/1/
Headers: Authorization: Bearer <token>
{
    "description": "مرض السكري من النوع الثاني - تحت السيطرة",
    "is_active": true
}

13. SEARCH DISEASES:
--------------------
GET /api/medical/diseases/?search=diabetes
GET /api/medical/diseases/?search=سكري

14. GET PATIENT'S CHRONIC DISEASES (Staff):
--------------------------------------------
GET /api/medical/chronic/by_patient/?patient=3

15. FILTER BY DISEASE CATEGORY:
--------------------------------
GET /api/medical/chronic/?disease__category=chronic&is_active=true

=============================================================================
Business Rules:
=============================================================================

1. COMMON DISEASES (Library):
   - Only Admin and Doctors can add/update/delete
   - All authenticated users can view
   - Cannot delete disease if assigned to patients
   - Unique Arabic and English names
   - Categories: chronic, infectious, genetic, other

2. CHRONIC DISEASES (Patient Records):
   - Only Doctors and Staff can create/update
   - Patients can view their own records only
   - Staff/Doctors can view all records
   - One record per patient per disease (unique constraint)
   - Cannot change patient or disease after creation
   - Can update: description, diagnosed_date, is_active

3. DISEASE STATUS:
   - is_active = true: Currently suffering from disease
   - is_active = false: Recovered or controlled
   - Doctors can activate/deactivate disease status

4. VIEW PERMISSIONS:
   - Patients: See only their chronic diseases
   - Doctors/Staff: See all records
   - Admin: Full access

5. VALIDATION:
   - Patient must be active with type='patient'
   - Diagnosed date cannot be in the future
   - Disease names must be unique
   - Cannot have duplicate disease for same patient

=============================================================================
Medical Categories:
=============================================================================

chronic (مزمن):
- Long-term diseases requiring ongoing management
- Examples: Diabetes, Hypertension, Asthma

infectious (معدي):
- Communicable diseases
- Examples: COVID-19, Tuberculosis, Hepatitis

genetic (وراثي):
- Inherited conditions
- Examples: Sickle Cell, Hemophilia, Thalassemia

other (أخرى):
- Other medical conditions
- Examples: Allergies, Injuries, Deficiencies

=============================================================================
"""