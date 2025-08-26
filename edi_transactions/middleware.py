# edi_transactions/middleware.py

import logging
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import CompanyUser, APIUsageLog

logger = logging.getLogger('edi_transactions.auth')


class CompanyMiddleware(MiddlewareMixin):
    """
    Middleware to handle multi-tenant company context and API usage tracking.
    """
    
    def process_request(self, request):
        """
        Add company context to request if user is authenticated.
        """
        # Skip for non-API requests and auth endpoints
        if not request.path.startswith('/api/') or '/auth/' in request.path:
            return None
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                company_user = CompanyUser.objects.select_related('company', 'company__subscription_plan').get(
                    user=request.user,
                    is_active=True
                )
                request.company_user = company_user
                request.company = company_user.company
                
                # Check company status
                company = company_user.company
                
                # Check if trial expired
                if (company.subscription_status == 'TRIAL' and 
                    company.subscription_end_date and 
                    company.subscription_end_date < timezone.now().date()):
                    
                    return JsonResponse({
                        'error': 'Trial subscription expired',
                        'detail': 'Please upgrade your subscription to continue using the service.',
                        'subscription_status': 'EXPIRED'
                    }, status=402)  # Payment Required
                
                # Check if subscription is suspended
                if company.subscription_status == 'SUSPENDED':
                    return JsonResponse({
                        'error': 'Subscription suspended',
                        'detail': 'Your subscription has been suspended. Please contact support.',
                        'subscription_status': 'SUSPENDED'
                    }, status=402)
                
                # Check if subscription is cancelled
                if company.subscription_status == 'CANCELLED':
                    return JsonResponse({
                        'error': 'Subscription cancelled',
                        'detail': 'Your subscription has been cancelled. Please reactivate to continue.',
                        'subscription_status': 'CANCELLED'
                    }, status=402)
                
            except CompanyUser.DoesNotExist:
                # User exists but no company association
                if '/profile/' not in request.path:  # Allow profile access for setup
                    return JsonResponse({
                        'error': 'No company association',
                        'detail': 'User is not associated with any company.'
                    }, status=403)
        
        return None
    
    def process_response(self, request, response):
        """
        Log API usage for authenticated users.
        """
        # Only log API endpoints
        if (hasattr(request, 'company_user') and 
            request.path.startswith('/api/') and 
            '/auth/' not in request.path):
            
            try:
                # Log API usage asynchronously in production
                self._log_api_usage(request, response)
            except Exception as e:
                logger.error(f"Failed to log API usage: {str(e)}")
        
        return response
    
    def _log_api_usage(self, request, response):
        """
        Log API usage for rate limiting and analytics.
        """
        try:
            # Get request size
            request_size = len(request.body) if hasattr(request, 'body') else 0
            
            # Get response size
            response_size = len(response.content) if hasattr(response, 'content') else 0
            
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0].strip()
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            APIUsageLog.objects.create(
                company=request.company_user.company,
                user=request.company_user,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_size_bytes=request_size,
                response_size_bytes=response_size,
            )
        except Exception as e:
            logger.error(f"Error logging API usage: {str(e)}")


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware based on subscription plan.
    """
    
    def process_request(self, request):
        """
        Check rate limits based on subscription plan.
        """
        # Skip for auth endpoints
        if '/auth/' in request.path or not request.path.startswith('/api/'):
            return None
        
        if hasattr(request, 'company_user'):
            company = request.company_user.company
            
            # Get current hour for rate limiting
            current_hour = timezone.now().replace(minute=0, second=0, microsecond=0)
            
            # Count requests in current hour
            hourly_requests = APIUsageLog.objects.filter(
                company=company,
                created_at__gte=current_hour
            ).count()
            
            # Set rate limits based on subscription
            rate_limits = {
                'trial': 100,
                'basic': 500,
                'growth': 2000,
                'enterprise': 10000,
            }
            
            plan_name = company.subscription_plan.name
            limit = rate_limits.get(plan_name, 100)
            
            if hourly_requests >= limit:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'detail': f'Hourly limit of {limit} requests exceeded. Please upgrade your plan.',
                    'limit': limit,
                    'remaining': 0,
                    'reset_time': (current_hour + timezone.timedelta(hours=1)).isoformat()
                }, status=429)
            
            # Add rate limit headers
            request.rate_limit_remaining = limit - hourly_requests
            request.rate_limit_limit = limit
        
        return None
    
    def process_response(self, request, response):
        """
        Add rate limit headers to response.
        """
        if hasattr(request, 'rate_limit_remaining'):
            response['X-RateLimit-Limit'] = str(request.rate_limit_limit)
            response['X-RateLimit-Remaining'] = str(request.rate_limit_remaining)
            response['X-RateLimit-Reset'] = str(int((timezone.now().replace(
                minute=0, second=0, microsecond=0
            ) + timezone.timedelta(hours=1)).timestamp()))
        
        return response


class SecurityMiddleware(MiddlewareMixin):
    """
    Additional security middleware for API endpoints.
    """
    
    def process_response(self, request, response):
        """
        Add security headers.
        """
        if request.path.startswith('/api/'):
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Add HSTS for HTTPS requests
            if request.is_secure():
                response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

        