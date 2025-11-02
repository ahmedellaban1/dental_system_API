"""
=============================================================================
payroll/urls.py - Payroll & Salary Management URLs
=============================================================================
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SalaryViewSet, AdvanceViewSet

# Create router
router = DefaultRouter()

# Register ViewSets
router.register(r'salaries', SalaryViewSet, basename='salary')
router.register(r'advances', AdvanceViewSet, basename='advance')

urlpatterns = [
    path('', include(router.urls)),
]

"""
=============================================================================
Available Endpoints:
=============================================================================

SALARIES - CRUD:
----------------
GET     /api/payroll/salaries/                - List salaries (filtered by role)
POST    /api/payroll/salaries/                - Create salary record (Admin)
GET     /api/payroll/salaries/{id}/           - Get salary details
PUT     /api/payroll/salaries/{id}/           - Update salary (Admin)
PATCH   /api/payroll/salaries/{id}/           - Partial update (Admin)
DELETE  /api/payroll/salaries/{id}/           - Delete salary (Admin)

SALARIES - Payment Actions:
---------------------------
POST    /api/payroll/salaries/{id}/mark_paid/ - Mark salary as paid (Admin)

SALARIES - Filtering & Views:
-----------------------------
GET     /api/payroll/salaries/my_salaries/    - Current receptionist's salaries
GET     /api/payroll/salaries/pending/        - Pending salaries
GET     /api/payroll/salaries/this_month/     - Current month salaries
GET     /api/payroll/salaries/by_receptionist/ - Salaries by receptionist (Admin)

SALARIES - Statistics:
----------------------
GET     /api/payroll/salaries/statistics/     - Salary statistics (Admin)

ADVANCES - CRUD:
----------------
GET     /api/payroll/advances/                - List advances (filtered by role)
POST    /api/payroll/advances/                - Request advance (Receptionist)
GET     /api/payroll/advances/{id}/           - Get advance details
DELETE  /api/payroll/advances/{id}/           - Delete pending advance (Admin)

ADVANCES - Approval Actions:
----------------------------
POST    /api/payroll/advances/{id}/approve/   - Approve advance (Admin)
POST    /api/payroll/advances/{id}/reject/    - Reject advance (Admin)
POST    /api/payroll/advances/{id}/mark_paid/ - Mark as paid (Admin)

ADVANCES - Filtering & Views:
-----------------------------
GET     /api/payroll/advances/my_advances/    - Current receptionist's advances
GET     /api/payroll/advances/pending/        - Pending advances
GET     /api/payroll/advances/approved/       - Approved advances

ADVANCES - Statistics:
----------------------
GET     /api/payroll/advances/statistics/         - Advance statistics (Admin)
GET     /api/payroll/advances/receptionist_summary/ - Receptionist summary (Admin)

=============================================================================
Query Parameters:
=============================================================================

Salaries:
---------
?status=pending                - Filter by status (pending/partial/paid)
?receptionist=1                - Filter by receptionist ID
?salary_month=2025-11-01       - Filter by month

Advances:
---------
?status=pending                - Filter by status (pending/approved/rejected/paid)
?receptionist=1                - Filter by receptionist ID
?search=emergency              - Search in reason

Ordering:
---------
?ordering=-salary_month        - Order by month (desc)
?ordering=net_salary           - Order by net salary (asc)
?ordering=-request_date        - Order by request date (desc)

Pagination:
-----------
?page=2                        - Page number
?page_size=10                  - Items per page (max 20)

=============================================================================
Example Requests:
=============================================================================

1. CREATE SALARY RECORD (Admin):
---------------------------------
POST /api/payroll/salaries/
Headers: Authorization: Bearer <token>
{
    "receptionist": 2,
    "base_salary": 5000.00,
    "bonus": 500.00,
    "deductions": 200.00,
    "salary_month": "2025-11-01",
    "status": "pending",
    "notes": "راتب شهر نوفمبر"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إنشاء سجل الراتب بنجاح / Salary record created successfully",
    "data": {
        "id": 1,
        "receptionist": 2,
        "receptionist_details": {
            "id": 2,
            "username": "receptionist1",
            "full_name": "فاطمة أحمد",
            "email": "fatma@clinic.com",
            "phone": "01098765432"
        },
        "base_salary": 5000.00,
        "bonus": 500.00,
        "deductions": 200.00,
        "net_salary": 5300.00,
        "salary_month": "2025-11-01",
        "month_display": "November 2025",
        "payment_date": null,
        "status": "pending",
        "status_display": "قيد الانتظار",
        "notes": "راتب شهر نوفمبر",
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

2. MARK SALARY AS PAID (Admin):
--------------------------------
POST /api/payroll/salaries/1/mark_paid/
Headers: Authorization: Bearer <token>
{
    "payment_date": "2025-11-01",
    "notes": "تم الدفع نقداً"
}

RESPONSE:
{
    "status": "success",
    "message": "تم تحديث حالة الراتب إلى مدفوع / Salary marked as paid",
    "data": { ... }
}

3. REQUEST ADVANCE (Receptionist):
-----------------------------------
POST /api/payroll/advances/
Headers: Authorization: Bearer <token>
{
    "amount": 1000.00,
    "reason": "ظروف عائلية طارئة تتطلب مبلغ عاجل"
}

RESPONSE:
{
    "status": "success",
    "message": "تم إرسال طلب السلفة بنجاح / Advance request submitted successfully",
    "data": {
        "id": 1,
        "receptionist": 2,
        "receptionist_details": {
            "id": 2,
            "username": "receptionist1",
            "full_name": "فاطمة أحمد",
            "email": "fatma@clinic.com",
            "phone": "01098765432"
        },
        "amount": 1000.00,
        "request_date": "2025-10-31",
        "payment_date": null,
        "status": "pending",
        "status_display": "قيد الانتظار",
        "reason": "ظروف عائلية طارئة تتطلب مبلغ عاجل",
        "approved_by": null,
        "approved_by_details": null,
        "notes": "",
        "created_at": "2025-10-31T12:00:00Z",
        "updated_at": "2025-10-31T12:00:00Z"
    }
}

4. APPROVE ADVANCE (Admin):
----------------------------
POST /api/payroll/advances/1/approve/
Headers: Authorization: Bearer <token>
{
    "payment_date": "2025-11-02",
    "notes": "تمت الموافقة"
}

RESPONSE:
{
    "status": "success",
    "message": "تم الموافقة على السلفة بنجاح / Advance approved successfully",
    "data": { ... }
}

5. REJECT ADVANCE (Admin):
---------------------------
POST /api/payroll/advances/1/reject/
Headers: Authorization: Bearer <token>
{
    "notes": "لا يوجد سيولة كافية حالياً"
}

6. GET MY SALARIES (Receptionist):
-----------------------------------
GET /api/payroll/salaries/my_salaries/
Headers: Authorization: Bearer <token>

RESPONSE:
{
    "status": "success",
    "message": "رواتبك / Your salaries",
    "data": [
        {
            "id": 1,
            "receptionist": 2,
            "receptionist_name": "فاطمة أحمد",
            "base_salary": 5000.00,
            "bonus": 500.00,
            "deductions": 200.00,
            "net_salary": 5300.00,
            "salary_month": "2025-11-01",
            "month_display": "November 2025",
            "payment_date": "2025-11-01",
            "status": "paid",
            "status_display": "مدفوع",
            "created_at": "2025-10-31T12:00:00Z"
        },
        ...
    ]
}

7. GET MY ADVANCES (Receptionist):
-----------------------------------
GET /api/payroll/advances/my_advances/

8. GET SALARY STATISTICS (Admin):
----------------------------------
GET /api/payroll/salaries/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات الرواتب / Salary statistics",
    "data": {
        "total_salaries": 120,
        "pending_salaries": 15,
        "partial_salaries": 5,
        "paid_salaries": 100,
        "total_amount": 600000.00,
        "total_paid": 500000.00,
        "total_pending": 100000.00,
        "this_month_total": 50000.00
    }
}

9. GET ADVANCE STATISTICS (Admin):
-----------------------------------
GET /api/payroll/advances/statistics/

RESPONSE:
{
    "status": "success",
    "message": "إحصائيات السلف / Advance statistics",
    "data": {
        "total_advances": 45,
        "pending_advances": 8,
        "approved_advances": 5,
        "rejected_advances": 12,
        "paid_advances": 20,
        "total_amount": 45000.00,
        "total_approved": 25000.00,
        "total_paid": 20000.00
    }
}

10. GET RECEPTIONIST PAYROLL SUMMARY (Admin):
----------------------------------------------
GET /api/payroll/advances/receptionist_summary/?receptionist=2

RESPONSE:
{
    "status": "success",
    "message": "ملخص رواتب فاطمة أحمد / Payroll summary for Fatma Ahmed",
    "data": {
        "receptionist_id": 2,
        "receptionist_name": "فاطمة أحمد",
        "total_salaries": 12,
        "total_earned": 63600.00,
        "total_advances": 5,
        "total_advance_amount": 5000.00,
        "pending_advances": 1
    }
}

11. GET THIS MONTH'S SALARIES:
------------------------------
GET /api/payroll/salaries/this_month/

12. GET PENDING SALARIES:
-------------------------
GET /api/payroll/salaries/pending/

13. GET PENDING ADVANCES:
-------------------------
GET /api/payroll/advances/pending/

14. GET APPROVED ADVANCES:
--------------------------
GET /api/payroll/advances/approved/

15. MARK ADVANCE AS PAID (Admin):
----------------------------------
POST /api/payroll/advances/1/mark_paid/

16. UPDATE SALARY (Admin):
--------------------------
PATCH /api/payroll/salaries/1/
{
    "bonus": 800.00,
    "notes": "مكافأة إضافية للأداء المتميز"
}

17. GET RECEPTIONIST'S SALARIES (Admin):
-----------------------------------------
GET /api/payroll/salaries/by_receptionist/?receptionist=2

=============================================================================
Business Rules:
=============================================================================

1. SALARY MANAGEMENT:
   - Only Admin can create/update/delete salary records
   - Receptionists can view their own salaries
   - One salary per receptionist per month (unique constraint)
   - Net salary auto-calculated: base_salary + bonus - deductions
   - Net salary cannot be negative
   - Salary month auto-corrected to first day of month
   - Status: pending → partial → paid

2. SALARY PAYMENT:
   - Only Admin can mark as paid
   - Payment date recorded
   - Cannot unpay after marking as paid

3. ADVANCE REQUESTS:
   - Only Receptionists can request advances
   - Must provide reason (min 10 characters)
   - Amount must be positive
   - Status starts as 'pending'

4. ADVANCE APPROVAL:
   - Only Admin can approve/reject
   - Can only approve/reject 'pending' advances
   - Approver tracked in approved_by field
   - Approved advances can be marked as paid
   - Status workflow:
     * pending → approved → paid
     * pending → rejected

5. VIEW PERMISSIONS:
   - Admin: See all salaries and advances
   - Receptionists: See only own salaries and advances

6. DELETION:
   - Only Admin can delete
   - Can only delete pending advances
   - Cannot delete paid salaries/advances

=============================================================================
Status Workflows:
=============================================================================

SALARY STATUS:
--------------
pending (قيد الانتظار)
   ↓
partial (جزئي) [optional]
   ↓
paid (مدفوع)

ADVANCE STATUS:
---------------
pending (قيد الانتظار)
   ↓
approved (موافق عليه) OR rejected (مرفوض)
   ↓
paid (مدفوع) [if approved]

=============================================================================
Calculations:
=============================================================================

NET SALARY:
-----------
net_salary = base_salary + bonus - deductions

Auto-calculated on save, cannot be manually set.

RECEPTIONIST SUMMARY:
---------------------
- Total salaries: Count of salary records
- Total earned: Sum of all net salaries
- Total advances: Count of advance requests
- Total advance amount: Sum of all advance amounts
- Pending advances: Count of pending requests

=============================================================================
"""