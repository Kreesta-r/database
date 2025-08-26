
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