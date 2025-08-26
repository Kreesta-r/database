# edi_transactions/utils/subscription.py

from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from ..models import SubscriptionPlan, Company


def create_trial_subscription(company_data):
    """Create a company with trial subscription"""
    trial_plan, created = SubscriptionPlan.objects.get_or_create(
        name='trial',
        defaults={
            'display_name': 'Trial Plan',
            'price_ngn': 0.00,
            'max_users': getattr(settings, 'MAX_TRIAL_USERS', 3),
            'max_transactions_monthly': getattr(settings, 'MAX_TRIAL_TRANSACTIONS', 100),
            'features': {
                'basic_edi': True,
                'trading_partners': 5,
                'reports': 'basic',
                'support': 'email',
                'api_access': True,
                'scbn_integration': True,
                'custom_reports': False,
                'sla_monitoring': False,
                'priority_support': False,
            }
        }
    )
    
    company_data['subscription_plan'] = trial_plan
    company_data['subscription_status'] = 'TRIAL'
    company_data['subscription_start_date'] = timezone.now().date()
    company_data['subscription_end_date'] = timezone.now().date() + timedelta(
        days=getattr(settings, 'TRIAL_DURATION_DAYS', 14)
    )
    
    return company_data


def check_subscription_limits(company, limit_type):
    """Check if company has reached subscription limits"""
    if limit_type == 'users':
        from ..models import CompanyUser
        current_count = CompanyUser.objects.filter(
            company=company,
            is_active=True
        ).count()
        max_count = company.subscription_plan.max_users
        
    elif limit_type == 'transactions':
        from ..models import EDITransaction
        current_month = timezone.now().replace(day=1)
        current_count = EDITransaction.objects.filter(
            company=company,
            created_at__gte=current_month
        ).count()
        max_count = company.subscription_plan.max_transactions_monthly
    
    else:
        return False, "Unknown limit type"
    
    if current_count >= max_count:
        return False, f"{limit_type.title()} limit reached ({max_count})"
    
    return True, f"{max_count - current_count} {limit_type} remaining"


def get_subscription_features(company):
    """Get available features for a company's subscription"""
    return company.subscription_plan.features or {}


def is_feature_available(company, feature_name):
    """Check if a specific feature is available for the company"""
    features = get_subscription_features(company)
    return features.get(feature_name, False)


# edi_transactions/utils/permissions.py

from django.core.exceptions import PermissionDenied
from functools import wraps
from ..models import CompanyUser


def company_required(view_func):
    """Decorator to ensure user has company association"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'company_user'):
            try:
                company_user = CompanyUser.objects.get(user=request.user, is_active=True)
                request.company_user = company_user
                request.company = company_user.company
            except CompanyUser.DoesNotExist:
                raise PermissionDenied("User not associated with any company")
        
        return view_func(request, *args, **kwargs)
    return wrapped_view


def role_required(*roles):
    """Decorator to check user role"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'company_user'):
                raise PermissionDenied("No company association")
            
            if request.company_user.role not in roles:
                raise PermissionDenied(f"Required role: {' or '.join(roles)}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def permission_required(permission):
    """Decorator to check specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'company_user'):
                raise PermissionDenied("No company association")
            
            permissions = request.company_user.permissions or {}
            if not permissions.get(permission, False):
                raise PermissionDenied(f"Missing permission: {permission}")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator


def feature_required(feature_name):
    """Decorator to check if subscription includes a feature"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            if not hasattr(request, 'company_user'):
                raise PermissionDenied("No company association")
            
            from ..subscription import is_feature_available
            if not is_feature_available(request.company_user.company, feature_name):
                raise PermissionDenied(f"Feature '{feature_name}' not available in your subscription plan")
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator
# edi_transactions/management/commands/create_subscription_plans.py

from django.core.management.base import BaseCommand
from edi_transactions.models import SubscriptionPlan


class Command(BaseCommand):
    help = 'Create default subscription plans'
    
    def handle(self, *args, **options):
        plans = [
            {
                'name': 'basic',
                'display_name': 'Basic Plan',
                'price_ngn': 25000.00,
                'max_users': 5,
                'max_transactions_monthly': 500,
                'features': {
                    'basic_edi': True,
                    'trading_partners': 10,
                    'reports': 'basic',
                    'support': 'email',
                    'api_access': True,
                    'scbn_integration': True,
                    'custom_reports': False,
                    'sla_monitoring': False,
                    'priority_support': False,
                }
            },
            {
                'name': 'growth',
                'display_name': 'Growth Plan',
                'price_ngn': 75000.00,
                'max_users': 15,
                'max_transactions_monthly': 2000,
                'features': {
                    'basic_edi': True,
                    'advanced_edi': True,
                    'trading_partners': 50,
                    'reports': 'advanced',
                    'support': 'priority',
                    'api_access': True,
                    'scbn_integration': True,
                    'custom_reports': True,
                    'sla_monitoring': True,
                    'priority_support': True,
                    'bulk_operations': True,
                }
            },
            {
                'name': 'enterprise',
                'display_name': 'Enterprise Plan',
                'price_ngn': 200000.00,
                'max_users': 100,
                'max_transactions_monthly': 10000,
                'features': {
                    'basic_edi': True,
                    'advanced_edi': True,
                    'premium_edi': True,
                    'trading_partners': -1,  # Unlimited
                    'reports': 'premium',
                    'support': '24/7',
                    'api_access': True,
                    'scbn_integration': True,
                    'custom_reports': True,
                    'sla_monitoring': True,
                    'priority_support': True,
                    'bulk_operations': True,
                    'white_labeling': True,
                    'dedicated_support': True,
                    'custom_integrations': True,
                }
            }
        ]
        
        for plan_data in plans:
            plan, created = SubscriptionPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"Created subscription plan: {plan.display_name}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"Subscription plan already exists: {plan.display_name}")
                )


# edi_transactions/management/commands/check_trial_expiry.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from edi_transactions.models import Company
from edi_transactions.utils.email import send_trial_expiry_warning


class Command(BaseCommand):
    help = 'Check for trial subscriptions expiring soon and send warning emails'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=3,
            help='Days before expiry to send warning (default: 3)'
        )
    
    def handle(self, *args, **options):
        warning_days = options['days']
        warning_date = timezone.now().date() + timedelta(days=warning_days)
        
        # Find trial companies expiring in specified days
        expiring_companies = Company.objects.filter(
            subscription_status='TRIAL',
            subscription_end_date=warning_date,
            is_active=True
        )
        
        for company in expiring_companies:
            days_remaining = (company.subscription_end_date - timezone.now().date()).days
            send_trial_expiry_warning(company, days_remaining)
            
            self.stdout.write(
                self.style.SUCCESS(f"Sent trial warning to {company.name} ({days_remaining} days remaining)")
            )
        
        if not expiring_companies:
            self.stdout.write(
                self.style.SUCCESS("No trials expiring in the specified timeframe")
            )