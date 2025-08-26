from django.utils import timezone

def is_feature_available(company, feature_name: str) -> bool:
    """
    Check if a given feature is available for a company's subscription plan.
    
    Args:
        company (Company): The company instance.
        feature_name (str): The feature to check (e.g. "invoices", "payments").
    
    Returns:
        bool: True if feature is available, False otherwise.
    """
    # Safety: company must have a subscription plan
    if not company.subscription_plan or not company.subscription_plan.is_active:
        return False

    # Check subscription status
    if company.subscription_status not in ["ACTIVE", "TRIAL"]:
        return False

    # Check subscription expiry (if set)
    if company.subscription_end_date and company.subscription_end_date < timezone.now().date():
        return False

    # Finally: check if feature exists in plan.features (JSONField)
    features = company.subscription_plan.features or []
    return feature_name in features
