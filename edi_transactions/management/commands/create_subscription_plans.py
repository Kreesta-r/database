
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