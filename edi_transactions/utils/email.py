# edi_transactions/utils/email.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger('edi_transactions.auth')


def send_welcome_email(user, company):
    """Send welcome email to new user"""
    try:
        subject = f"Welcome to {settings.DEFAULT_FROM_EMAIL.split('@')[0].title()}!"
        
        context = {
            'user': user,
            'company': company,
            'trial_days': settings.TRIAL_DURATION_DAYS,
            'support_email': settings.DEFAULT_FROM_EMAIL,
        }
        
        html_message = render_to_string('emails/welcome.html', context)
        plain_message = render_to_string('emails/welcome.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")


def send_trial_expiry_warning(company, days_remaining):
    """Send trial expiry warning email"""
    try:
        admin_users = company.companyuser_set.filter(role='ADMIN', is_active=True)
        
        for company_user in admin_users:
            subject = f"Your trial expires in {days_remaining} days"
            
            context = {
                'user': company_user.user,
                'company': company,
                'days_remaining': days_remaining,
                'upgrade_url': f"{settings.FRONTEND_URL}/subscription/upgrade",
            }
            
            html_message = render_to_string('emails/trial_warning.html', context)
            plain_message = render_to_string('emails/trial_warning.txt', context)
            
            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[company_user.user.email],
                fail_silently=False,
            )
        
        logger.info(f"Trial warning email sent to {company.name} admins")
        
    except Exception as e:
        logger.error(f"Failed to send trial warning email to {company.name}: {str(e)}")

