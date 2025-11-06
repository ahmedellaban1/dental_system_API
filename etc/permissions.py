"""
=============================================================================
permissions.py - Centralized Permission Classes
All custom permissions for the dental system API
=============================================================================
"""

from rest_framework import permissions


# ======================== Base Role Permissions ========================

class IsAdmin(permissions.BasePermission):
    """
    Permission: Only system administrators
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'admin'


class IsDoctor(permissions.BasePermission):
    """
    Permission: Only doctors
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'doctor'


class IsPatient(permissions.BasePermission):
    """
    Permission: Only patients
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'patient'


class IsReceptionist(permissions.BasePermission):
    """
    Permission: Only receptionists
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'receptionist'


class IsMedicalRep(permissions.BasePermission):
    """
    Permission: Only medical representatives
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'medical_rep'


# ======================== Combined Permissions ========================

class IsAdminOrDoctor(permissions.BasePermission):
    """
    Permission: Admin or Doctor only
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type in ['admin', 'doctor']
        )


class IsAdminOrReceptionist(permissions.BasePermission):
    """
    Permission: Admin or Receptionist only
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type in ['admin', 'receptionist']
        )


class IsStaff(permissions.BasePermission):
    """
    Permission: Any staff member (admin, doctor, receptionist)
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type in ['admin', 'doctor', 'receptionist']
        )


class IsStaffOrMedicalRep(permissions.BasePermission):
    """
    Permission: Staff or medical rep
    """

    def has_permission(self, request, view):
        return (
                request.user.is_authenticated and
                request.user.type in ['admin', 'doctor', 'receptionist', 'medical_rep']
        )


# ======================== Account Management Permissions ========================

class CanCreateDoctorAccount(permissions.BasePermission):
    """
    Permission: Only admin can create doctor accounts
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.type == 'admin'
        return True


class CanCreateReceptionistAccount(permissions.BasePermission):
    """
    Permission: Only admin can create receptionist accounts
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.type == 'admin'
        return True


class CanCreateMedicalRepAccount(permissions.BasePermission):
    """
    Permission: Only admin can create medical rep accounts
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.type == 'admin'
        return True


class CanCreatePatientAccount(permissions.BasePermission):
    """
    Permission: Admin or Receptionist can create patient accounts
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return (
                    request.user.is_authenticated and
                    request.user.type in ['admin', 'receptionist']
            )
        return True


# ======================== Profile Permissions ========================

class IsOwnerOrStaff(permissions.BasePermission):
    """
    Permission: Owner of profile or staff member
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view/edit any profile
        if request.user.type in ['admin', 'doctor', 'receptionist']:
            return True
        # Users can only access their own profile
        return obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission: Owner can edit, others can only read
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions only for owner
        return obj.user == request.user


# ======================== Read-Only Permissions ========================

class ReadOnlyForPatients(permissions.BasePermission):
    """
    Permission: Patients can only read, staff can write
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Patients can only read
        if request.user.type == 'patient':
            return request.method in permissions.SAFE_METHODS

        # Staff can do everything
        return request.user.type in ['admin', 'doctor', 'receptionist']


# ======================== Activation Permissions ========================

class CanActivateUsers(permissions.BasePermission):
    """
    Permission: Only admin can activate/deactivate users
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'admin'


# ======================== Appointment Permissions ========================

class CanCreateBooking(permissions.BasePermission):
    """
    Permission: Admin, Receptionist can create bookings for any patient
    Patients can only create bookings for themselves
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            if not request.user.is_authenticated:
                return False

            # Staff can create bookings for anyone
            if request.user.type in ['admin', 'receptionist']:
                return True

            # Patients can only create for themselves
            if request.user.type == 'patient':
                patient_id = request.data.get('patient')
                return patient_id is None or int(patient_id) == request.user.id

            return False
        return True


class CanViewBooking(permissions.BasePermission):
    """
    Permission: Staff can view all bookings
    Doctors can view their own bookings
    Patients can view their own bookings
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view all bookings
        if request.user.type in ['admin', 'receptionist']:
            return True

        # Doctors can view their bookings
        if request.user.type == 'doctor':
            return obj.doctor == request.user

        # Patients can view their bookings
        if request.user.type == 'patient':
            return obj.patient == request.user

        return False


class CanUpdateBooking(permissions.BasePermission):
    """
    Permission: Admin and Receptionist can update any booking
    Doctors can update status of their bookings
    Patients can update their own pending bookings
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin and Receptionist can update any booking
        if request.user.type in ['admin', 'receptionist']:
            return True

        # Doctors can update their bookings (mainly status and notes)
        if request.user.type == 'doctor' and obj.doctor == request.user:
            return True

        # Patients can update their own pending bookings only
        if request.user.type == 'patient' and obj.patient == request.user:
            return obj.status == 'pending'

        return False


class CanCancelBooking(permissions.BasePermission):
    """
    Permission: Staff can cancel any booking
    Patients can cancel their own bookings
    Doctors can cancel their bookings
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can cancel any booking
        if request.user.type in ['admin', 'receptionist']:
            return True

        # Doctors can cancel their bookings
        if request.user.type == 'doctor' and obj.doctor == request.user:
            return True

        # Patients can cancel their own bookings
        if request.user.type == 'patient' and obj.patient == request.user:
            return obj.status in ['pending', 'confirmed']

        return False


# ======================== Billing Permissions ========================

class CanCreateBill(permissions.BasePermission):
    """
    Permission: Only staff can create bills
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.type in ['admin', 'receptionist']
        return True


class CanViewBill(permissions.BasePermission):
    """
    Permission: Staff can view all bills, Patients can view their own bills
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view all bills
        if request.user.type in ['admin', 'receptionist']:
            return True

        # Patients can view their own bills
        if request.user.type == 'patient':
            return obj.patient == request.user

        return False


class CanUpdateBill(permissions.BasePermission):
    """
    Permission: Only staff can update bills
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in ['admin', 'receptionist']

    def has_object_permission(self, request, view, obj):
        return request.user.type in ['admin', 'receptionist']


class CanProcessPayment(permissions.BasePermission):
    """
    Permission: Only staff can process payments
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in ['admin', 'receptionist']


# ======================== Medical Records Permissions ========================

class CanManageCommonDiseases(permissions.BasePermission):
    """
    Permission: Only admin and doctors can manage common diseases library
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.type in ['admin', 'doctor']


class CanViewMedicalRecord(permissions.BasePermission):
    """
    Permission: Staff and doctors can view all records, patients can view own
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view all records
        if request.user.type in ['admin', 'receptionist', 'doctor']:
            return True

        # Patients can view their own records
        if request.user.type == 'patient':
            return obj.patient == request.user

        return False


class CanManageMedicalRecord(permissions.BasePermission):
    """
    Permission: Only doctors and staff can create/update medical records
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in ['admin', 'doctor', 'receptionist']

    def has_object_permission(self, request, view, obj):
        # Admin can manage all records
        if request.user.type == 'admin':
            return True

        # Doctors can manage records
        if request.user.type == 'doctor':
            return True

        # Receptionists can view but limited updates
        if request.user.type == 'receptionist':
            return request.method in permissions.SAFE_METHODS

        return False


# ======================== Operations Permissions ========================

class CanViewOperation(permissions.BasePermission):
    """
    Permission: Staff and doctors can view all operations, patients can view their own
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view all operations
        if request.user.type in ['admin', 'receptionist']:
            return True

        # Doctors can view their operations
        if request.user.type == 'doctor':
            return obj.doctor == request.user

        # Patients can view their operations
        if request.user.type == 'patient':
            return obj.patient == request.user

        return False


class CanManageOperation(permissions.BasePermission):
    """
    Permission: Doctors and admin can create/update operations
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in ['admin', 'doctor']

    def has_object_permission(self, request, view, obj):
        # Admin can manage all operations
        if request.user.type == 'admin':
            return True

        # Doctors can manage their own operations
        if request.user.type == 'doctor':
            return obj.doctor == request.user

        return False


class CanManageOperationMedia(permissions.BasePermission):
    """
    Permission: Doctors and admin can manage operation media
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in ['admin', 'doctor']

    def has_object_permission(self, request, view, obj):
        # Admin can manage all media
        if request.user.type == 'admin':
            return True

        # Doctors can manage media for their operations
        if request.user.type == 'doctor':
            return obj.operation.doctor == request.user

        return False


# ======================== Payroll Permissions ========================

class CanManageSalary(permissions.BasePermission):
    """
    Permission: Only admin can manage salaries
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # Receptionists can view their own salaries
            if request.user.type == 'receptionist':
                return True
            # Admin can view all
            return request.user.is_authenticated and request.user.type == 'admin'
        # Only admin can create/update/delete
        return request.user.is_authenticated and request.user.type == 'admin'

    def has_object_permission(self, request, view, obj):
        # Admin can do everything
        if request.user.type == 'admin':
            return True

        # Receptionists can only view their own salaries
        if request.user.type == 'receptionist':
            return request.method in permissions.SAFE_METHODS and obj.receptionist == request.user

        return False


class CanViewAdvance(permissions.BasePermission):
    """
    Permission: Admin can view all, receptionists can view own
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type in ['admin', 'receptionist']

    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.type == 'admin':
            return True

        # Receptionists can view their own advances
        if request.user.type == 'receptionist':
            return obj.receptionist == request.user

        return False


class CanRequestAdvance(permissions.BasePermission):
    """
    Permission: Only receptionists can request advances
    """

    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.type == 'receptionist'
        return True


class CanApproveAdvance(permissions.BasePermission):
    """
    Permission: Only admin can approve/reject advances
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'admin'


# ======================== Pharmacy Permissions ========================

class CanManageMedicineLibrary(permissions.BasePermission):
    """
    Permission: Admin and doctors can manage medicine library
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.type in ['admin', 'doctor']


class CanViewPrescription(permissions.BasePermission):
    """
    Permission: Staff/doctors can view all, patients can view own
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Staff can view all
        if request.user.type in ['admin', 'receptionist']:
            return True

        # Doctors can view their prescriptions
        if request.user.type == 'doctor':
            return obj.doctor == request.user

        # Patients can view their prescriptions
        if request.user.type == 'patient':
            return obj.patient == request.user

        return False


class CanManagePrescription(permissions.BasePermission):
    """
    Permission: Only doctors can create/update prescriptions
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.type == 'doctor'

    def has_object_permission(self, request, view, obj):
        # Doctors can only manage their own prescriptions
        return obj.doctor == request.user