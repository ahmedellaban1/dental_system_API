"""
=============================================================================
accounts/serializers.py - Account Management Serializers with JWT
=============================================================================
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from cities_light.models import City
from .models import CustomUser, Profile
from etc.validators import (
    validate_password_strength,
    validate_egyptian_phone,
    validate_age,
    validate_file_size,
    validate_image_file
)


# ======================== City Serializer ========================

class CitySerializer(serializers.ModelSerializer):
    """
    Nested serializer for City information
    """
    country = serializers.CharField(source='country.name', read_only=True)
    region = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = City
        fields = ['id', 'name', 'country', 'region']
        read_only_fields = ['id', 'name', 'country', 'region']


# ======================== Profile Serializers ========================

class ProfileSerializer(serializers.ModelSerializer):
    """
    Profile serializer with nested city info
    """
    city_details = CitySerializer(source='city', read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'image', 'city', 'city_details', 'address', 'phone',
            'date_of_birth', 'age', 'gender', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'city': {'write_only': True}
        }

    def get_age(self, obj):
        """Calculate age from date_of_birth"""
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - obj.date_of_birth.year
            if (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day):
                age -= 1
            return age
        return None

    def validate_phone(self, value):
        """Validate Egyptian phone number"""
        try:
            validate_egyptian_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_date_of_birth(self, value):
        """Validate age is reasonable"""
        try:
            validate_age(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_image(self, value):
        """Validate image file"""
        if value:
            try:
                validate_file_size(value)
                validate_image_file(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating profile (excludes user field)
    """
    city_details = CitySerializer(source='city', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'image', 'city', 'city_details', 'address', 'phone',
            'date_of_birth', 'gender'
        ]
        extra_kwargs = {
            'city': {'write_only': True}
        }

    def validate_phone(self, value):
        try:
            validate_egyptian_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_date_of_birth(self, value):
        try:
            validate_age(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_image(self, value):
        if value:
            try:
                validate_file_size(value)
                validate_image_file(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value


# ======================== User Serializers ========================

class UserListSerializer(serializers.ModelSerializer):
    """
    Minimal user serializer for lists
    """
    profile_image = serializers.ImageField(source='user_profile.image', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'type', 'is_active', 'profile_image', 'date_joined']
        read_only_fields = fields


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Detailed user serializer with profile
    """
    profile = ProfileSerializer(source='user_profile', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'type', 'is_active', 'date_joined', 'last_login', 'profile'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


# ======================== JWT Token Serializers ========================

class TokenObtainSerializer(serializers.Serializer):
    """
    Login serializer with JWT tokens
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # Authenticate user
        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError(
                "اسم المستخدم أو كلمة المرور غير صحيحة / Invalid username or password"
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "الحساب غير مفعل. يرجى الاتصال بالإدارة / Account is inactive. Please contact admin"
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class TokenRefreshSerializer(serializers.Serializer):
    """
    Refresh token serializer
    """
    refresh = serializers.CharField(required=True)

    def validate(self, attrs):
        from rest_framework_simplejwt.tokens import RefreshToken
        from rest_framework_simplejwt.exceptions import TokenError

        try:
            refresh = RefreshToken(attrs['refresh'])
            data = {
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }
            return data
        except TokenError:
            raise serializers.ValidationError(
                "رمز التحديث غير صالح أو منتهي الصلاحية / Invalid or expired refresh token"
            )


class UserWithTokenSerializer(serializers.ModelSerializer):
    """
    User serializer with JWT tokens (for registration/login responses)
    """
    profile = ProfileSerializer(source='user_profile', read_only=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'type', 'is_active', 'date_joined', 'profile', 'tokens'
        ]
        read_only_fields = fields

    def get_tokens(self, obj):
        """Generate JWT tokens for user"""
        refresh = RefreshToken.for_user(obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


# ======================== User Creation Serializers ========================

class BaseUserCreateSerializer(serializers.ModelSerializer):
    """
    Base serializer for user creation with profile data
    """
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)

    # Profile fields
    phone = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    date_of_birth = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=['male', 'female'], required=True)
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.all(),
        required=False,
        allow_null=True
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'address',
            'date_of_birth', 'gender', 'city', 'image'
        ]

    def validate(self, attrs):
        """Validate passwords match"""
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({
                "password_confirm": "كلمات المرور غير متطابقة / Passwords do not match"
            })

        # Validate password strength
        try:
            validate_password_strength(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"password": str(e)})

        return attrs

    def validate_phone(self, value):
        try:
            validate_egyptian_phone(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_date_of_birth(self, value):
        try:
            validate_age(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate_image(self, value):
        if value:
            try:
                validate_file_size(value)
                validate_image_file(value)
            except DjangoValidationError as e:
                raise serializers.ValidationError(str(e))
        return value

    def create(self, validated_data):
        """Create user and profile"""
        # Extract profile data
        profile_data = {
            'phone': validated_data.pop('phone'),
            'address': validated_data.pop('address'),
            'date_of_birth': validated_data.pop('date_of_birth'),
            'gender': validated_data.pop('gender'),
            'city': validated_data.pop('city', None),
            'image': validated_data.pop('image', None),
        }

        # Create user
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()

        # Update profile (created by signal)
        Profile.objects.filter(user=user).update(**profile_data)

        return user


class PatientCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating patient accounts
    Created by: Admin or Receptionist
    """
    class Meta(BaseUserCreateSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['type'] = 'patient'
        return super().create(validated_data)


class DoctorCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating doctor accounts
    Created by: Admin only
    """
    class Meta(BaseUserCreateSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['type'] = 'doctor'
        return super().create(validated_data)


class ReceptionistCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating receptionist accounts
    Created by: Admin only
    """
    class Meta(BaseUserCreateSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['type'] = 'receptionist'
        return super().create(validated_data)


class MedicalRepCreateSerializer(BaseUserCreateSerializer):
    """
    Serializer for creating medical rep accounts
    Created by: Admin only
    """
    class Meta(BaseUserCreateSerializer.Meta):
        pass

    def create(self, validated_data):
        validated_data['type'] = 'medical_rep'
        return super().create(validated_data)


# ======================== Password Change Serializer ========================

class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing password
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password_confirm": "كلمات المرور غير متطابقة / Passwords do not match"
            })

        try:
            validate_password_strength(attrs['new_password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": str(e)})

        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                "كلمة المرور القديمة غير صحيحة / Old password is incorrect"
            )
        return value


# ======================== User Activation Serializer ========================

class UserActivationSerializer(serializers.Serializer):
    """
    Serializer for activating/deactivating users
    """
    is_active = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)