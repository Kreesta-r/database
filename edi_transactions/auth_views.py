# edi_transactions/views/auth_views.py

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import datetime, timedelta
import secrets
import logging

from .models import Company, CompanyUser, SubscriptionPlan
from .serializers import (
    CustomTokenObtainPairSerializer, 
    RegisterSerializer, 
    CompanyRegistrationSerializer,
    UserProfileSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer
)
from .permissions import IsCompanyUser
from .utils.subscriptions import create_trial_subscription, check_subscription_limits

logger = logging.getLogger('edi_transactions.auth')


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view with company context"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful login
            user = authenticate(
                username=request.data.get('username'),
                password=request.data.get('password')
            )
            if user:
                try:
                    company_user = CompanyUser.objects.get(user=user)
                    logger.info(f"User {user.username} logged in for company {company_user.company.name}")
                except CompanyUser.DoesNotExist:
                    logger.warning(f"User {user.username} logged in but no company association found")
        
        return response


class RegisterView(APIView):
    """User registration with company creation"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            with db_transaction.atomic():
                # Validate company data
                company_serializer = CompanyRegistrationSerializer(data=request.data.get('company', {}))
                if not company_serializer.is_valid():
                    return Response({
                        'error': 'Company data validation failed',
                        'company_errors': company_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Validate user data
                user_serializer = RegisterSerializer(data=request.data.get('user', {}))
                if not user_serializer.is_valid():
                    return Response({
                        'error': 'User data validation failed',
                        'user_errors': user_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Check if user already exists
                if User.objects.filter(username=user_serializer.validated_data['username']).exists():
                    return Response({
                        'error': 'User with this username already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if User.objects.filter(email=user_serializer.validated_data['email']).exists():
                    return Response({
                        'error': 'User with this email already exists'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create user
                user = User.objects.create_user(
                    username=user_serializer.validated_data['username'],
                    email=user_serializer.validated_data['email'],
                    password=user_serializer.validated_data['password'],
                    first_name=user_serializer.validated_data.get('first_name', ''),
                    last_name=user_serializer.validated_data.get('last_name', ''),
                )
                
                # Create trial subscription plan if it doesn't exist
                trial_plan, created = SubscriptionPlan.objects.get_or_create(
                    name='trial',
                    defaults={
                        'display_name': 'Trial Plan',
                        'price_ngn': 0.00,
                        'max_users': settings.MAX_TRIAL_USERS,
                        'max_transactions_monthly': settings.MAX_TRIAL_TRANSACTIONS,
                        'features': {
                            'basic_edi': True,
                            'trading_partners': 5,
                            'reports': 'basic',
                            'support': 'email'
                        }
                    }
                )
                
                # Create company with trial subscription
                company_data = company_serializer.validated_data
                company_data['subscription_plan'] = trial_plan
                company_data['subscription_status'] = 'TRIAL'
                company_data['subscription_start_date'] = timezone.now().date()
                company_data['subscription_end_date'] = timezone.now().date() + timedelta(days=settings.TRIAL_DURATION_DAYS)
                
                company = Company.objects.create(**company_data)
                
                # Create company user with admin role
                company_user = CompanyUser.objects.create(
                    company=company,
                    user=user,
                    role='ADMIN',
                    permissions={
                        'can_manage_users': True,
                        'can_manage_partners': True,
                        'can_view_reports': True,
                        'can_manage_settings': True
                    }
                )
                
                # Generate verification token (optional)
                verification_token = secrets.token_urlsafe(32)
                # Store this in a separate model if you want email verification
                
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                
                # Log successful registration
                logger.info(f"New company registered: {company.name} by user {user.username}")
                
                return Response({
                    'message': 'Registration successful',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'company': {
                        'id': company.id,
                        'name': company.name,
                        'subscription_status': company.subscription_status,
                        'trial_ends': company.subscription_end_date,
                    },
                    'tokens': {
                        'access': str(refresh.access_token),
                        'refresh': str(refresh),
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                'error': 'Registration failed',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(APIView):
    """Get and update user profile"""
    permission_classes = [IsCompanyUser]
    
    def get(self, request):
        try:
            company_user = CompanyUser.objects.get(user=request.user)
            serializer = UserProfileSerializer(company_user)
            return Response(serializer.data)
        except CompanyUser.DoesNotExist:
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request):
        try:
            company_user = CompanyUser.objects.get(user=request.user)
            serializer = UserProfileSerializer(company_user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CompanyUser.DoesNotExist:
            return Response({
                'error': 'User profile not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CompanyStatusView(APIView):
    """Get company subscription status and limits"""
    permission_classes = [IsCompanyUser]
    
    def get(self, request):
        try:
            company_user = CompanyUser.objects.get(user=request.user)
            company = company_user.company
            
            # Check current usage
            current_month = timezone.now().replace(day=1)
            
            # Get transaction count for current month
            from .models import EDITransaction
            monthly_transactions = EDITransaction.objects.filter(
                company=company,
                created_at__gte=current_month
            ).count()
            
            # Get active user count
            active_users = CompanyUser.objects.filter(
                company=company,
                is_active=True
            ).count()
            
            # Calculate days remaining for trial
            days_remaining = None
            if company.subscription_status == 'TRIAL' and company.subscription_end_date:
                days_remaining = (company.subscription_end_date - timezone.now().date()).days
            
            return Response({
                'company': {
                    'id': company.id,
                    'name': company.name,
                    'subscription_plan': company.subscription_plan.display_name,
                    'subscription_status': company.subscription_status,
                    'subscription_end_date': company.subscription_end_date,
                    'days_remaining': days_remaining,
                },
                'limits': {
                    'max_users': company.subscription_plan.max_users,
                    'current_users': active_users,
                    'max_transactions_monthly': company.subscription_plan.max_transactions_monthly,
                    'current_transactions': monthly_transactions,
                    'users_available': company.subscription_plan.max_users - active_users,
                    'transactions_available': company.subscription_plan.max_transactions_monthly - monthly_transactions,
                },
                'features': company.subscription_plan.features,
            })
            
        except CompanyUser.DoesNotExist:
            return Response({
                'error': 'Company not found'
            }, status=status.HTTP_404_NOT_FOUND)


class PasswordResetView(APIView):
    """Request password reset"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email)
                
                # Generate reset token
                reset_token = secrets.token_urlsafe(32)
                
                # Here you would store the reset token in a model
                # For now, we'll just send it via email
                
                # Send password reset email
                send_mail(
                    subject='Password Reset Request',
                    message=f'Your password reset token: {reset_token}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                logger.info(f"Password reset requested for user {user.username}")
                
                return Response({
                    'message': 'Password reset email sent'
                })
                
            except User.DoesNotExist:
                # Don't reveal that the user doesn't exist
                return Response({
                    'message': 'If a user with this email exists, a password reset email has been sent'
                })
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            # Here you would validate the token and reset the password
            # This is a simplified implementation
            
            return Response({
                'message': 'Password has been reset successfully'
            })
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """Logout user and blacklist refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User {request.user.username} logged out")
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({
                'error': 'Error logging out'
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def subscription_plans(request):
    """Get available subscription plans"""
    plans = SubscriptionPlan.objects.filter(is_active=True).exclude(name='trial')
    
    plans_data = []
    for plan in plans:
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'display_name': plan.display_name,
            'price_ngn': float(plan.price_ngn),
            'max_users': plan.max_users,
            'max_transactions_monthly': plan.max_transactions_monthly,
            'features': plan.features,
        })
    
    return Response({
        'plans': plans_data
    })


@api_view(['POST'])
@permission_classes([IsCompanyUser])
def upgrade_subscription(request):
    """Upgrade subscription plan"""
    try:
        company_user = CompanyUser.objects.get(user=request.user)
        company = company_user.company
        
        # Check if user has admin permissions
        if company_user.role != 'ADMIN':
            return Response({
                'error': 'Only company administrators can upgrade subscriptions'
            }, status=status.HTTP_403_FORBIDDEN)
        
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({
                'error': 'Plan ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            new_plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({
                'error': 'Invalid subscription plan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update company subscription
        company.subscription_plan = new_plan
        company.subscription_status = 'ACTIVE'
        company.subscription_start_date = timezone.now().date()
        company.subscription_end_date = None  # For monthly billing, this would be set
        company.save()
        
        logger.info(f"Company {company.name} upgraded to {new_plan.display_name}")
        
        return Response({
            'message': 'Subscription upgraded successfully',
            'company': {
                'subscription_plan': new_plan.display_name,
                'subscription_status': company.subscription_status,
            }
        })
        
    except CompanyUser.DoesNotExist:
        return Response({
            'error': 'Company not found'
        }, status=status.HTTP_404_NOT_FOUND)