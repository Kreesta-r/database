# edi_transactions/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Company, CompanyUser, SubscriptionPlan


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include company information"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add custom claims
        try:
            company_user = CompanyUser.objects.get(user=self.user)
            data['company'] = {
                'id': company_user.company.id,
                'name': company_user.company.name,
                'subscription_status': company_user.company.subscription_status,
                'role': company_user.role,
            }
            data['user_profile'] = {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'role': company_user.role,
                'permissions': company_user.permissions,
            }
        except CompanyUser.DoesNotExist:
            pass
            
        return data


class RegisterSerializer(serializers.Serializer):
    """User registration serializer"""
    username = serializers.CharField(
        min_length=3,
        max_length=150,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text="Password must be at least 8 characters long."
    )
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Password fields didn't match."
            })
        return attrs


class CompanyRegistrationSerializer(serializers.Serializer):
    """Company registration serializer"""
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    industry = serializers.CharField(max_length=100, required=False, allow_blank=True)
    company_size = serializers.ChoiceField(
        choices=Company.COMPANY_SIZE_CHOICES,
        required=False,
        allow_blank=True
    )
    
    # Address fields
    address_line1 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_line2 = serializers.CharField(max_length=255, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    state = serializers.CharField(max_length=100, required=False, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    def validate_name(self, value):
        if Company.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("A company with this name already exists.")
        return value
    
    def validate(self, attrs):
        # Build address JSON if any address fields are provided
        address_fields = ['address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country']
        address_data = {field: attrs.pop(field, '') for field in address_fields if field in attrs}
        
        if any(address_data.values()):
            attrs['address'] = address_data
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    user = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyUser
        fields = [
            'id', 'user', 'company', 'role', 'permissions', 
            'phone', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'company']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'date_joined': obj.user.date_joined,
            'last_login': obj.user.last_login,
        }
    
    def get_company(self, obj):
        return {
            'id': obj.company.id,
            'name': obj.company.name,
            'subscription_plan': obj.company.subscription_plan.display_name,
            'subscription_status': obj.company.subscription_status,
        }
    
    def update(self, instance, validated_data):
        # Update user fields if provided
        user_data = self.context['request'].data.get('user', {})
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.email = user_data.get('email', user.email)
            user.save()
        
        # Update CompanyUser fields
        instance.phone = validated_data.get('phone', instance.phone)
        instance.save()
        
        return instance


class PasswordResetSerializer(serializers.Serializer):
    """Password reset request serializer"""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Password fields didn't match."
            })
        return attrs


class CompanyUserSerializer(serializers.ModelSerializer):
    """Company user management serializer"""
    user = serializers.SerializerMethodField()
    
    class Meta:
        model = CompanyUser
        fields = [
            'id', 'user', 'role', 'permissions', 'phone', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'last_login': obj.user.last_login,
        }


class InviteUserSerializer(serializers.Serializer):
    """Invite new user to company serializer"""
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=CompanyUser.ROLE_CHOICES)
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Subscription plan serializer"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'display_name', 'price_ngn', 'max_users', 
            'max_transactions_monthly', 'features', 'is_active'
        ]
        read_only_fields = ['id']