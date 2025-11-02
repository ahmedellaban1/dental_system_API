"""
=============================================================================
billing/urls.py - Billing & Payment Management URLs
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BillViewSet

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'bills', BillViewSet, basename='bill')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

BILLS - CRUD Operations:
------------------------
GET     /api/billing/bills/                  - List bills (filtered by role)
POST    /api/billing/bills/                  - Create new bill (Staff only)
GET     /api/billing/bills/{id}/             - Get bill details
PUT     /api/billing/bills/{id}/             - Update bill (Staff only)
PATCH   /api/billing/bills/{id}/             - Partial update bill (Staff only)
DELETE  /api/billing/bills/{id}/             - Delete bill (Admin only)

BILLS - Payment Actions:
------------------------
POST    /api/billing/bills/{id}/process_payment/ - Process payment (Staff only)
POST    /api/billing/bills/{id}/mark_paid/       - Mark as fully paid (Staff only)

BILLS - Filtering & Views:
--------------------------
GET     /api/billing/bills/my_bills/         - Get current patient's bills
GET     /api/billing/bills/unpaid/           - Get unpaid bills
GET     /api/billing/bills/partial/          - Get partially paid bills
GET     /api/billing/bills/overdue/          - Get overdue bills

BILLS - Statistics & Reports:
-----------------------------
GET     /api/billing/bills/summary/          - Get billing summary (Staff only)
GET     /api/billing/bills/by_patient/       - Get bills by patient (Staff only)
GET     /api/billing/bills/payment_methods/  - Payment method statistics (Staff only)
GET     /api/billing/bills/monthly_revenue/  - Monthly revenue (Staff only)
GET     /api/billing/bills/today_revenue/    - Today's revenue (Staff only)

=============================================================================
Query Parameters:
=============================================================================

Filtering:
----------
?payment_status=unpaid         - Filter by status (unpaid/partial/paid)
?payment_method=cash           - Filter by payment method
?patient=1                     - Filter by patient ID
?operation=5                   - Filter by operation ID

Search:
-------
?search=ahmed                  - Search in patient name, notes

Ordering:
---------
?ordering=-bill_date           - Order by bill date (desc)
?ordering=remaining_amount     - Order by remaining amount (asc)
?ordering=-total_amount        - Order by total amount (desc)

Pagination:
-----------
?page=2                        - Page number
?page_size=10                  - Items per page (max 20)

=============================================================================
Example Requests:
=============================================================================

1. CREATE BILL (Staff):
-----------------------
POST /api/billing/bills/
Headers: Authorization: Bearer <token>
{
    "patient": 3,
    "booking": 10,
    "operation": 5,
    "paid_amount": 500.00,
    "payment_method": "cash",
    "due_date": "2025-12-01",
    "notes": "دفعة مقدمة / Down payment"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إنشاء الفاتورة بنجاح / Bill created successfully",
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
        "created_by": 2,
        "created_by_details": {
            "id": 2,
            "username": "receptionist1",
            "full_name": "فاطمة أحمد"
        },
        "booking": 10,
        "booking_details": {
            "id": 10,
            "appointment_datetime": "2025-11-15T10:00:00Z",
            "doctor_name": "د. أحمد السيد",
            "status": "completed"
        },
        "operation": 5,
        "operation_details": {
            "id": 5,
            "operation_name": "تنظيف الأسنان",
            "operation_cost": 1000.00,
            "status": "completed"
        },
        "total_amount": 1000.00,
        "paid_amount": 500.00,
        "remaining_amount": 500.00,
        "payment_status": "partial",
        "payment_status_display": "مدفوع جزئياً",
        "payment_method": "cash",
        "payment_method_display": "نقدي",
        "bill_date": "2025-10-31",
        "due_date": "2025-12-01",
        "notes": "دفعة مقدمة / Down payment",
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

2. PROCESS PAYMENT (Staff):
----------------------------
POST /api/billing/bills/1/process_payment/
Headers: Authorization: Bearer <token>
{
    "amount": 500.00,
    "payment_method": "card",
    "notes": "دفعة نهائية / Final payment"
}

RESPONSE:
{
    "status": "success",
    "message": "تم تسجيل الدفع بنجاح / Payment processed successfully",
    "data": {
        "id": 1,
        "total_amount": 1000.00,
        "paid_amount": 1000.00,
        "remaining_amount": 0.00,
        "payment_status": "paid",
        "payment_status_display": "مدفوع بالكامل",
        "payment_method": "card",
        "payment_method_display": "بطاقة ائتمان",
        ...
    }
}

3. MARK AS PAID (Staff):
-------------------------
POST /api/billing/bills/1/mark_paid/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "تم تحديث حالة الفاتورة إلى مدفوع / Bill marked as paid",
    "data": { ... }
}

4. GET MY BILLS (Patient):
---------------------------
GET /api/billing/bills/my_bills/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "تم جلب فواتيرك بنجاح / Your bills retrieved successfully",
    "data": [
        {
            "id": 1,
            "patient": 3,
            "patient_name": "أحمد محمد",
            "total_amount": 1000.00,
            "paid_amount": 500.00,
            "remaining_amount": 500.00,
            "payment_status": "partial",
            "payment_status_display": "مدفوع جزئياً",
            "payment_method": "cash",
            "payment_method_display": "نقدي",
            "bill_date": "2025-10-31",
            "due_date": "2025-12-01"
        },
        ...
    ]
}

5. GET UNPAID BILLS:
--------------------
GET /api/billing/bills/unpaid/

6. GET OVERDUE BILLS:
---------------------
GET /api/billing/bills/overdue/

7. GET BILLING SUMMARY (Staff):
--------------------------------
GET /api/billing/bills/summary/

RESPONSE:
{
    "status": "success",
    "message": "ملخص الفواتير / Billing summary",
    "data": {
        "total_bills": 150,
        "total_amount": 150000.00,
        "total_paid": 120000.00,
        "total_remaining": 30000.00,
        "unpaid_bills": 20,
        "partial_bills": 35,
        "paid_bills": 95,
        "overdue_bills": 12
    }
}

8. GET PATIENT BILL SUMMARY (Staff):
-------------------------------------
GET /api/billing/bills/by_patient/?patient=3

RESPONSE:
{
    "status": "success",
    "message": "ملخص فواتير أحمد محمد / Bill summary for Ahmed Mohamed",
    "data": {
        "patient_id": 3,
        "patient_name": "أحمد محمد",
        "total_bills": 5,
        "total_amount": 5000.00,
        "total_paid": 3500.00,
        "total_remaining": 1500.00,
        "unpaid_count": 1,
        "partial_count": 2,
        "paid_count": 2
    }
}

9. GET PAYMENT METHOD STATISTICS (Staff):
------------------------------------------
GET /api/billing/bills/payment_methods/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات طرق الدفع / Payment method statistics",
    "data": [
        {
            "payment_method": "cash",
            "payment_method_display": "نقدي",
            "count": 80,
            "total_amount": 50000.00
        },
        {
            "payment_method": "card",
            "payment_method_display": "بطاقة ائتمان",
            "count": 45,
            "total_amount": 35000.00
        },
        {
            "payment_method": "vodafone_cash",
            "payment_method_display": "فودافون كاش",
            "count": 25,
            "total_amount": 15000.00
        },
        ...
    ]
}

10. GET MONTHLY REVENUE (Staff):
---------------------------------
GET /api/billing/bills/monthly_revenue/

RESPONSE:
{
    "status": "success",
    "message": "الإيرادات الشهرية / Monthly revenue",
    "data": [
        {
            "month": "October",
            "year": 2025,
            "total_billed": 45000.00,
            "total_collected": 38000.00,
            "total_pending": 7000.00,
            "bill_count": 45
        },
        {
            "month": "September",
            "year": 2025,
            "total_billed": 52000.00,
            "total_collected": 48000.00,
            "total_pending": 4000.00,
            "bill_count": 52
        },
        ...
    ]
}

11. GET TODAY'S REVENUE (Staff):
---------------------------------
GET /api/billing/bills/today_revenue/

RESPONSE:
{
    "status": "success",
    "message": "إيرادات اليوم (2025-10-31) / Today's revenue (2025-10-31)",
    "data": {
        "date": "2025-10-31",
        "total_billed": 5000.00,
        "total_collected": 3500.00,
        "bill_count": 5
    }
}

12. UPDATE BILL (Staff):
-------------------------
PATCH /api/billing/bills/1/
Headers: Authorization: Bearer <token>
{
    "paid_amount": 750.00,
    "payment_method": "instapay",
    "notes": "تحديث الدفعة / Payment update"
}

13. GET FILTERED BILLS:
------------------------
GET /api/billing/bills/?payment_status=partial&patient=3&ordering=-bill_date

14. GET BILLS BY OPERATION:
----------------------------
GET /api/billing/bills/?operation=5

15. SEARCH BILLS:
-----------------
GET /api/billing/bills/?search=ahmed

=============================================================================
Business Rules:
=============================================================================

1. BILL CREATION:
   - Only staff can create bills
   - Patient must be active with type='patient'
   - Operation must have a valid cost > 0
   - Paid amount cannot exceed total amount
   - Auto-set created_by to current user
   - Booking (optional) must belong to patient

2. BILL UPDATES:
   - Only staff can update bills
   - Cannot update operation (linked to completed operation)
   - Paid amount validation:
     * Cannot be negative
     * Cannot exceed total amount from operation cost

3. PAYMENT PROCESSING:
   - Only staff can process payments
   - Cannot pay already fully paid bills
   - Payment amount must be > 0
   - Payment cannot exceed remaining amount
   - Auto-updates:
     * paid_amount += payment amount
     * remaining_amount = total - paid
     * payment_status (unpaid/partial/paid)

4. AUTO-CALCULATIONS:
   - total_amount = operation.cost (readonly property)
   - remaining_amount = total_amount - paid_amount
   - payment_status:
     * unpaid: paid_amount = 0
     * partial: 0 < paid_amount < total_amount
     * paid: paid_amount >= total_amount

5. VIEW PERMISSIONS:
   - Patients: See only their bills
   - Staff: See all bills

6. OVERDUE DETECTION:
   - Bill is overdue if:
     * due_date < today
     * payment_status = unpaid OR partial

=============================================================================
Validation Rules:
=============================================================================

1. Patient must be active and type='patient'
2. Operation must exist and have cost > 0
3. Paid amount >= 0 and <= total amount
4. Booking (if provided) must belong to patient
5. Payment method required when paid_amount > 0
6. Payment processing amount must be > 0 and <= remaining

=============================================================================
"""