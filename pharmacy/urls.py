"""
=============================================================================
pharmacy/urls.py - Pharmacy & Prescription Management URLs
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicineLibraryViewSet, PrescriptionViewSet

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'medicines', MedicineLibraryViewSet, basename='medicine')
router.register(r'prescriptions', PrescriptionViewSet, basename='prescription')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

MEDICINE LIBRARY - CRUD:
-------------------------
GET     /api/pharmacy/medicines/              - List medicines
POST    /api/pharmacy/medicines/              - Add medicine (Admin/Doctor)
GET     /api/pharmacy/medicines/{id}/         - Get medicine details
PUT     /api/pharmacy/medicines/{id}/         - Update medicine (Admin/Doctor)
PATCH   /api/pharmacy/medicines/{id}/         - Partial update (Admin/Doctor)
DELETE  /api/pharmacy/medicines/{id}/         - Delete medicine (Admin/Doctor)

MEDICINE LIBRARY - Filtering & Views:
--------------------------------------
GET     /api/pharmacy/medicines/by_form/      - Medicines by form
GET     /api/pharmacy/medicines/most_prescribed/ - Most prescribed medicines
GET     /api/pharmacy/medicines/statistics/   - Medicine statistics (Staff)

PRESCRIPTIONS - CRUD:
---------------------
GET     /api/pharmacy/prescriptions/          - List prescriptions (filtered by role)
POST    /api/pharmacy/prescriptions/          - Create prescription (Doctor)
GET     /api/pharmacy/prescriptions/{id}/     - Get prescription details
PUT     /api/pharmacy/prescriptions/{id}/     - Update prescription (Doctor - own)
PATCH   /api/pharmacy/prescriptions/{id}/     - Partial update (Doctor - own)
DELETE  /api/pharmacy/prescriptions/{id}/     - Delete prescription (Admin)

PRESCRIPTIONS - Filtering & Views:
-----------------------------------
GET     /api/pharmacy/prescriptions/my_prescriptions/ - Current user's prescriptions
GET     /api/pharmacy/prescriptions/today/    - Today's prescriptions
GET     /api/pharmacy/prescriptions/by_doctor/ - Prescriptions by doctor (Staff)
GET     /api/pharmacy/prescriptions/by_patient/ - Prescriptions by patient (Staff)

PRESCRIPTIONS - Statistics:
---------------------------
GET     /api/pharmacy/prescriptions/statistics/ - Prescription statistics (Staff)
GET     /api/pharmacy/prescriptions/doctor_statistics/ - Stats by doctor (Staff)

=============================================================================
Query Parameters:
=============================================================================

Medicines:
----------
?form=tablet                   - Filter by form
?search=aspirin                - Search in name, active ingredient
?ordering=-times_prescribed    - Order by times prescribed (desc)
?ordering=trade_name           - Order by name (asc)

Prescriptions:
--------------
?patient=1                     - Filter by patient ID
?doctor=5                      - Filter by doctor ID
?prescription_date=2025-11-01  - Filter by date
?search=diabetes               - Search in patient name, diagnosis

Pagination:
-----------
?page=2                        - Page number
?page_size=10                  - Items per page (max 20)

=============================================================================
Example Requests:
=============================================================================

1. ADD MEDICINE TO LIBRARY (Admin/Doctor):
-------------------------------------------
POST /api/pharmacy/medicines/
Headers: Authorization: Bearer <token>
{
    "trade_name": "بانادول / Panadol",
    "active_ingredient": "Paracetamol",
    "strength": "500mg",
    "form": "tablet",
    "description": "مسكن للألم وخافض للحرارة",
    "indications": "الصداع، الحمى، آلام الجسم",
    "contraindications": "الحساسية تجاه الباراسيتامول",
    "side_effects": "نادراً: طفح جلدي، غثيان"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إضافة الدواء بنجاح / Medicine added successfully",
    "data": {
        "id": 1,
        "trade_name": "بانادول / Panadol",
        "active_ingredient": "Paracetamol",
        "strength": "500mg",
        "form": "tablet",
        "form_display": "قرص",
        "description": "مسكن للألم وخافض للحرارة",
        "indications": "الصداع، الحمى، آلام الجسم",
        "contraindications": "الحساسية تجاه الباراسيتامول",
        "side_effects": "نادراً: طفح جلدي، غثيان",
        "times_prescribed": 0,
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

2. CREATE PRESCRIPTION (Doctor):
---------------------------------
POST /api/pharmacy/prescriptions/
Headers: Authorization: Bearer <token>
{
    "patient": 3,
    "booking": 10,
    "diagnosis": "التهاب اللثة",
    "instructions": "يُنصح بالمضمضة بالماء الدافئ والملح",
    "items": [
        {
            "medicine": 1,
            "dosage": "500mg",
            "frequency": "3 مرات يومياً بعد الأكل",
            "duration_days": 7,
            "instructions": "مع كوب ماء كامل"
        },
        {
            "medicine": 5,
            "dosage": "400mg",
            "frequency": "مرتين يومياً",
            "duration_days": 5,
            "instructions": "قبل الأكل بنصف ساعة"
        }
    ]
}

RESPONSE:
{
    "status": "success",
    "message": "تم إنشاء الروشتة بنجاح / Prescription created successfully",
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
        "prescription_date": "2025-10-31",
        "diagnosis": "التهاب اللثة",
        "instructions": "يُنصح بالمضمضة بالماء الدافئ والملح",
        "items": [
            {
                "id": 1,
                "medicine": 1,
                "medicine_details": {
                    "id": 1,
                    "trade_name": "بانادول / Panadol",
                    "active_ingredient": "Paracetamol",
                    "strength": "500mg",
                    "form": "tablet",
                    "form_display": "قرص",
                    "times_prescribed": 1
                },
                "dosage": "500mg",
                "frequency": "3 مرات يومياً بعد الأكل",
                "duration_days": 7,
                "instructions": "مع كوب ماء كامل",
                "created_at": "2025-10-31T12:00:00Z"
            },
            {
                "id": 2,
                "medicine": 5,
                "medicine_details": { ... },
                "dosage": "400mg",
                "frequency": "مرتين يومياً",
                "duration_days": 5,
                "instructions": "قبل الأكل بنصف ساعة",
                "created_at": "2025-10-31T12:00:00Z"
            }
        ],
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

3. GET MY PRESCRIPTIONS (Patient or Doctor):
---------------------------------------------
GET /api/pharmacy/prescriptions/my_prescriptions/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "روشتاتك / Your prescriptions",
    "data": [
        {
            "id": 1,
            "patient": 3,
            "patient_name": "أحمد محمد",
            "doctor": 5,
            "doctor_name": "د. أحمد السيد",
            "prescription_date": "2025-10-31",
            "items_count": 2,
            "created_at": "2025-10-31T12:00:00Z"
        },
        ...
    ]
}

4. GET MOST PRESCRIBED MEDICINES:
----------------------------------
GET /api/pharmacy/medicines/most_prescribed/?limit=10

RESPONSE:
{
    "status": "success",
    "message": "الأدوية الأكثر وصفاً / Most prescribed medicines",
    "data": [
        {
            "id": 1,
            "trade_name": "بانادول / Panadol",
            "active_ingredient": "Paracetamol",
            "strength": "500mg",
            "form": "tablet",
            "form_display": "قرص",
            "times_prescribed": 145,
            "created_at": "2025-01-15T10:00:00Z"
        },
        ...
    ]
}

5. GET MEDICINE STATISTICS (Staff):
------------------------------------
GET /api/pharmacy/medicines/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات مكتبة الأدوية / Medicine library statistics",
    "data": {
        "total_medicines": 250,
        "by_form": {
            "قرص": 120,
            "كبسولة": 45,
            "شراب": 35,
            "حقن": 25,
            "كريم": 25
        },
        "most_prescribed": [
            {
                "id": 1,
                "trade_name": "بانادول / Panadol",
                "active_ingredient": "Paracetamol",
                "times_prescribed": 145
            },
            ...
        ]
    }
}

6. GET PRESCRIPTION STATISTICS (Staff):
----------------------------------------
GET /api/pharmacy/prescriptions/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات الروشتات / Prescription statistics",
    "data": {
        "total_prescriptions": 450,
        "today_prescriptions": 12,
        "this_month_prescriptions": 85,
        "total_items": 1250,
        "avg_items_per_prescription": 2.78
    }
}

7. GET DOCTOR PRESCRIPTION STATISTICS (Staff):
-----------------------------------------------
GET /api/pharmacy/prescriptions/doctor_statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات الأطباء / Doctor statistics",
    "data": [
        {
            "doctor_id": 5,
            "doctor_name": "د. أحمد السيد",
            "total_prescriptions": 185,
            "total_items": 520
        },
        ...
    ]
}

8. GET TODAY'S PRESCRIPTIONS:
------------------------------
GET /api/pharmacy/prescriptions/today/

9. GET PATIENT'S PRESCRIPTIONS (Staff):
----------------------------------------
GET /api/pharmacy/prescriptions/by_patient/?patient=3

10. GET DOCTOR'S PRESCRIPTIONS (Staff):
----------------------------------------
GET /api/pharmacy/prescriptions/by_doctor/?doctor=5

11. GET MEDICINES BY FORM:
---------------------------
GET /api/pharmacy/medicines/by_form/?form=tablet

12. UPDATE PRESCRIPTION (Doctor - own):
----------------------------------------
PATCH /api/pharmacy/prescriptions/1/
Headers: Authorization: Bearer <token>
{
    "diagnosis": "التهاب اللثة الحاد",
    "instructions": "يُنصح بالمضمضة بالماء الدافئ والملح 3 مرات يومياً"
}

13. SEARCH MEDICINES:
---------------------
GET /api/pharmacy/medicines/?search=panadol
GET /api/pharmacy/medicines/?search=باراسيتامول

14. FILTER PRESCRIPTIONS:
--------------------------
GET /api/pharmacy/prescriptions/?patient=3&prescription_date=2025-10-31

=============================================================================
Business Rules:
=============================================================================

1. MEDICINE LIBRARY:
   - Only Admin and Doctors can add/update/delete
   - All authenticated users can view
   - Unique combination of trade_name + strength
   - Cannot delete medicine used in prescriptions
   - times_prescribed auto-increments when added to prescription

2. PRESCRIPTIONS:
   - Only Doctors can create prescriptions
   - Must include at least one medicine item
   - Doctor auto-set from logged-in user
   - Booking (optional) must belong to patient
   - Doctors can only update their own prescriptions (diagnosis/instructions)
   - Cannot update items after creation

3. PRESCRIPTION ITEMS:
   - Auto-increments medicine.times_prescribed on creation
   - Duration must be 1-365 days
   - Dosage, frequency, and duration required

4. VIEW PERMISSIONS:
   - Patients: See only their prescriptions
   - Doctors: See only their prescriptions
   - Staff: See all prescriptions

5. AUTO-COUNTERS:
   - times_prescribed increments when medicine added to prescription
   - Cannot be manually changed

=============================================================================
Medicine Forms:
=============================================================================

tablet (قرص):
- Solid oral dosage form
- Most common form

capsule (كبسولة):
- Gelatin shell containing medicine
- Easy to swallow

syrup (شراب):
- Liquid oral medication
- Often for children

injection (حقن):
- Injectable medication
- IV, IM, or subcutaneous

cream (كريم):
- Topical application
- For skin conditions

=============================================================================
Integration with Other Apps:
=============================================================================

1. APPOINTMENTS:
   - Prescription can link to Booking
   - Optional relationship

2. ACCOUNTS:
   - Patient and Doctor from CustomUser
   - Type validation enforced

3. MEDICAL:
   - Diagnosis can reference chronic diseases
   - Prescription supports treatment tracking

=============================================================================
🎉 COMPLETE DENTAL CLINIC API - ALL 7 APPS READY! 🎉
=============================================================================

✅ 1. accounts       - Users & Authentication
✅ 2. appointments   - Booking System
✅ 3. billing        - Invoices & Payments
✅ 4. medical        - Diseases & Records
✅ 5. operations     - Procedures & Media
✅ 6. payroll        - Salaries & Advances
✅ 7. pharmacy       - Medicines & Prescriptions

Total: 50+ Endpoints | 7 Apps | Complete CRUD | Role-Based Access
Arabic + English | JWT Auth | Statistics | File Uploads | Auto-Calculations

🚀 Ready for Production!
=============================================================================
"""