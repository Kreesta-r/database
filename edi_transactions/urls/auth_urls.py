# edi_transactions/urls/auth_urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from ..auth_views import (
    CustomTokenObtainPairView,
    RegisterView,
    UserProfileView,
    CompanyStatusView,
    PasswordResetView,
    PasswordResetConfirmView,
    LogoutView,
    subscription_plans,
    upgrade_subscription,
)

app_name = 'auth' 

urlpatterns = [
    # Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Registration
    path('register/', RegisterView.as_view(), name='register'),
    
    # Profile Management
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('company/status/', CompanyStatusView.as_view(), name='company_status'),
    
    # Password Reset
    path('password/reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Subscription Management
    path('subscription/plans/', subscription_plans, name='subscription_plans'),
    path('subscription/upgrade/', upgrade_subscription, name='upgrade_subscription'),
]