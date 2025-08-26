# edi_transactions/permissions.py

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from .models import CompanyUser


class IsCompanyUser(permissions.BasePermission):
    """
    Custom permission to only allow users associated with a company.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            company_user = CompanyUser.objects.get(user=request.user, is_active=True)
            
            # Check if company subscription is valid
            company = company_user.company
            if company.subscription_status == 'SUSPENDED':
                raise PermissionDenied("Company subscription is suspended.")
            
            if company.subscription_status == 'CANCELLED':
                raise PermissionDenied("Company subscription has been cancelled.")
            
            # Check if trial has expired
            if (company.subscription_status == 'TRIAL' and 
                company.subscription_end_date and 
                company.subscription_end_date < timezone.now().date()):
                raise PermissionDenied("Trial subscription has expired. Please upgrade your plan.")
            
            # Add company_user to request for easy access in views
            request.company_user = company_user
            return True
            
        except CompanyUser.DoesNotExist:
            return False


class IsCompanyAdmin(IsCompanyUser):
    """
    Custom permission for company administrators only.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        return request.company_user.role == 'ADMIN'


class IsCompanyManagerOrAdmin(IsCompanyUser):
    """
    Custom permission for company managers and administrators.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        return request.company_user.role in ['ADMIN', 'MANAGER']


class HasSubscriptionFeature(IsCompanyUser):
    """
    Permission class to check if company has access to specific features.
    Usage: Add feature_name as class attribute.
    """
    feature_name = None
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        if not self.feature_name:
            return True
        
        company = request.company_user.company
        features = company.subscription_plan.features or {}
        
        if not features.get(self.feature_name, False):
            raise PermissionDenied(f"This feature ({self.feature_name}) is not available in your subscription plan.")
        
        return True


class CheckTransactionLimit(IsCompanyUser):
    """
    Permission class to check transaction limits.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        # Only check for POST requests (creating new transactions)
        if request.method != 'POST':
            return True
        
        company = request.company_user.company
        
        # Get current month transactions
        current_month = timezone.now().replace(day=1)
        from .models import EDITransaction
        
        monthly_count = EDITransaction.objects.filter(
            company=company,
            created_at__gte=current_month
        ).count()
        
        if monthly_count >= company.subscription_plan.max_transactions_monthly:
            raise PermissionDenied(
                f"Monthly transaction limit ({company.subscription_plan.max_transactions_monthly}) reached. "
                "Please upgrade your subscription plan."
            )
        
        return True


class CheckUserLimit(IsCompanyAdmin):
    """
    Permission class to check user limits when adding new users.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        # Only check for POST requests (creating new users)
        if request.method != 'POST':
            return True
        
        company = request.company_user.company
        
        # Count active users
        active_users = CompanyUser.objects.filter(
            company=company,
            is_active=True
        ).count()
        
        if active_users >= company.subscription_plan.max_users:
            raise PermissionDenied(
                f"User limit ({company.subscription_plan.max_users}) reached. "
                "Please upgrade your subscription plan."
            )
        
        return True


class CanManageUsers(IsCompanyUser):
    """
    Permission for user management operations.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        # Check role-based access
        if request.company_user.role not in ['ADMIN', 'MANAGER']:
            return False
        
        # Check specific permission
        permissions = request.company_user.permissions or {}
        return permissions.get('can_manage_users', False)


class CanManagePartners(IsCompanyUser):
    """
    Permission for trading partner management.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        permissions = request.company_user.permissions or {}
        return permissions.get('can_manage_partners', False)


class CanViewReports(IsCompanyUser):
    """
    Permission for viewing reports.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        permissions = request.company_user.permissions or {}
        return permissions.get('can_view_reports', False)


class CanManageSettings(IsCompanyAdmin):
    """
    Permission for managing company settings.
    """
    
    def has_permission(self, request, view):
        has_basic_permission = super().has_permission(request, view)
        if not has_basic_permission:
            return False
        
        permissions = request.company_user.permissions or {}
        return permissions.get('can_manage_settings', False)