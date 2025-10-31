"""
=============================================================================
accounts/views.py - Account Management Views
=============================================================================
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from .models import CustomUser, Profile
from .serializers import (
    UserListSerializer, UserDetailSerializer,
    PatientCreateSerializer, DoctorCreateSerializer,
    ReceptionistCreateSerializer, MedicalRepCreateSerializer,
    ProfileSerializer, ProfileUpdateSerializer,
    PasswordChangeSerializer, UserActivationSerializer
)
from etc.permissions import (
    IsAdmin, IsAdminOrReceptionist, IsOwnerOrStaff,
    CanActivateUsers
)
from etc.responses import success, created, bad_request, not_found, forbidden
from etc.paginator_classes import DefaultPagination


# ======================== User Management ViewSets ========================

class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient accounts
    - List/Retrieve: Staff only
    - Create: Admin or Receptionist
    - Update/Delete: Admin only
    """
    queryset = CustomUser.objects.filter(type='patient').select_related('user_profile', 'user_profile__city')
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'user_profile__gender', 'user_profile__city']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'user_profile__phone']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return PatientCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminOrReceptionist()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم استرجاع قائمة المرضى بنجاح ",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم استرجاع بيانات المريض بنجاح  ",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return created(
                message="تم إنشاء حساب المريض بنجاح",
                data=UserDetailSerializer(user).data
            )
        return bad_request(
            message="فشل إنشاء الحساب",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات المريض بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات المريض بنجاح ",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف حساب المريض بنجاح "
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """Activate/Deactivate patient account"""
        user = self.get_object()
        serializer = UserActivationSerializer(data=request.data)

        if serializer.is_valid():
            user.is_active = serializer.validated_data['is_active']
            user.save()

            status_text = "تفعيل" if user.is_active else "إلغاء تفعيل"
            return success(
                message=f"تم {status_text} الحساب بنجاح / Account {status_text} successfully",
                data=UserDetailSerializer(user).data
            )
        return bad_request(errors=serializer.errors)


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor accounts
    - List/Retrieve: Staff only
    - Create/Update/Delete: Admin only
    """
    queryset = CustomUser.objects.filter(type='doctor').select_related('user_profile', 'user_profile__city')
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'user_profile__gender']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'user_profile__phone']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return DoctorCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'activate']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم استرجاء قائمة الأطباء بنجاح ",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم استرجاع بيانات الطبيب بنجاح",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return created(
                message="تم إنشاء حساب الطبيب بنجاح / Doctor account created successfully",
                data=UserDetailSerializer(user).data
            )
        return bad_request(
            message="فشل إنشاء الحساب ",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات الطبيب بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات الطبيب بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث ",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف حساب الطبيب بنجاح "
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """Activate/Deactivate doctor account"""
        user = self.get_object()
        serializer = UserActivationSerializer(data=request.data)

        if serializer.is_valid():
            user.is_active = serializer.validated_data['is_active']
            user.save()

            status_text = "تفعيل " if user.is_active else "إلغاء تفعيل"
            return success(
                message=f"تم {status_text} الحساب بنجاح / Account {status_text} successfully",
                data=UserDetailSerializer(user).data
            )
        return bad_request(errors=serializer.errors)


class ReceptionistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing receptionist accounts
    - List/Retrieve: Staff only
    - Create/Update/Delete: Admin only
    """
    queryset = CustomUser.objects.filter(type='receptionist').select_related('user_profile', 'user_profile__city')
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'user_profile__gender']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'user_profile__phone']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return ReceptionistCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'activate']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم استرجاع قائمة موظفي الاستقبال بنجاح",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم استرجاع بيانات موظف الاستقبال بنجاح ",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return created(
                message="تم إنشاء حساب موظف الاستقبال بنجاح",
                data=UserDetailSerializer(user).data
            )
        return bad_request(
            message="فشل إنشاء الحساب",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات موظف الاستقبال بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات موظف الاستقبال بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف حساب موظف الاستقبال بنجاح"
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """Activate/Deactivate receptionist account"""
        user = self.get_object()
        serializer = UserActivationSerializer(data=request.data)

        if serializer.is_valid():
            user.is_active = serializer.validated_data['is_active']
            user.save()

            status_text = "تفعيل / activated" if user.is_active else "إلغاء تفعيل / deactivated"
            return success(
                message=f"تم {status_text} الحساب بنجاح / Account {status_text} successfully",
                data=UserDetailSerializer(user).data
            )
        return bad_request(errors=serializer.errors)


class MedicalRepViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medical rep accounts
    - List/Retrieve: Staff only
    - Create/Update/Delete: Admin only
    """
    queryset = CustomUser.objects.filter(type='medical_rep').select_related('user_profile', 'user_profile__city')
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'user_profile__gender']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'user_profile__phone']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    def get_serializer_class(self):
        if self.action == 'create':
            return MedicalRepCreateSerializer
        elif self.action == 'list':
            return UserListSerializer
        return UserDetailSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'activate']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم استرجاع قائمة المندوبين الطبيين بنجاح",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم استرجاع بيانات المندوب الطبي بنجاح",
            data=serializer.data
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return created(
                message="تم إنشاء حساب المندوب الطبي بنجاح",
                data=UserDetailSerializer(user).data
            )
        return bad_request(
            message="فشل إنشاء الحساب ",
            errors=serializer.errors
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات المندوب الطبي بنجاح ",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث / Update failed",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث بيانات المندوب الطبي بنجاح ",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return success(
            message="تم حذف حساب المندوب الطبي بنجاح"
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def activate(self, request, pk=None):
        """Activate/Deactivate medical rep account"""
        user = self.get_object()
        serializer = UserActivationSerializer(data=request.data)

        if serializer.is_valid():
            user.is_active = serializer.validated_data['is_active']
            user.save()

            status_text = "تفعيل" if user.is_active else "إلغاء تفعيل"
            return success(
                message=f"تم {status_text} الحساب بنجاح / Account {status_text} successfully",
                data=UserDetailSerializer(user).data
            )
        return bad_request(errors=serializer.errors)


# ======================== Profile ViewSet ========================

class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles
    - List/Retrieve: Authenticated users
    - Update: Owner or Staff
    """
    queryset = Profile.objects.select_related('user', 'city').all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = DefaultPagination

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProfileUpdateSerializer
        return ProfileSerializer

    def get_queryset(self):
        # Patients can only see their own profile
        if self.request.user.type == 'patient':
            return Profile.objects.filter(user=self.request.user)
        # Staff can see all profiles
        return Profile.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success(
            message="تم جلب الملفات الشخصية بنجاح",
            data=serializer.data
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return success(
            message="تم جلب الملف الشخصي بنجاح",
            data=serializer.data
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check permission
        if request.user.type == 'patient' and instance.user != request.user:
            return forbidden(message="لا يمكنك تعديل ملف شخصي آخر")

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث الملف الشخصي بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check permission
        if request.user.type == 'patient' and instance.user != request.user:
            return forbidden(message="لا يمكنك تعديل ملف شخصي آخر ")

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success(
                message="تم تحديث الملف الشخصي بنجاح",
                data=serializer.data
            )
        return bad_request(
            message="فشل التحديث",
            errors=serializer.errors
        )

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        profile = get_object_or_404(Profile, user=request.user)
        serializer = self.get_serializer(profile)
        return success(
            message="تم جلب ملفك الشخصي بنجاح",
            data=serializer.data
        )

    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change current user's password"""
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            return success(
                message="تم تغيير كلمة المرور بنجاح"
            )
        return bad_request(
            message="فشل تغيير كلمة المرور",
            errors=serializer.errors
        )