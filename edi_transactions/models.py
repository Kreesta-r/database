from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth.models import User


# =============================================
# CORE TENANT & SUBSCRIPTION MANAGEMENT
# =============================================

class SubscriptionPlan(models.Model):
    """Subscription Plans (Basic, Growth, Enterprise)"""
    
    class Meta:
        db_table = 'subscription_plans'
        
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)  # 'basic', 'growth', 'enterprise'
    display_name = models.CharField(max_length=100)
    price_ngn = models.DecimalField(max_digits=10, decimal_places=2)
    max_users = models.IntegerField()
    max_transactions_monthly = models.IntegerField()
    features = models.JSONField()  # Store plan features as JSON
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.display_name


class Company(models.Model):
    """Companies (Main Tenant Entity)"""
    
    COMPANY_SIZE_CHOICES = [
        ('SMALL', 'Small (1-50 employees)'),
        ('MEDIUM', 'Medium (51-250 employees)'),
        ('LARGE', 'Large (251-1000 employees)'),
        ('ENTERPRISE', 'Enterprise (1000+ employees)'),
    ]
    
    SUBSCRIPTION_STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('CANCELLED', 'Cancelled'),
        ('TRIAL', 'Trial'),
    ]
    
    class Meta:
        db_table = 'companies'
        verbose_name_plural = 'companies'
        indexes = [
            models.Index(fields=['subscription_plan'], name='idx_comp_sub_plan'),
            models.Index(fields=['scbn_mailbox_id'], name='idx_comp_scbn_id'),
        ]
        
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    address = models.JSONField(blank=True, null=True)  # Complete address as JSON
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, blank=True, null=True)
    
    # Subscription Info
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    subscription_status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS_CHOICES, default='ACTIVE')
    subscription_start_date = models.DateField(blank=True, null=True)
    subscription_end_date = models.DateField(blank=True, null=True)
    
    # SCBN Integration
    scbn_mailbox_id = models.CharField(max_length=100, unique=True, blank=True, null=True)
    scbn_credentials = models.JSONField(blank=True, null=True)  # Encrypted credentials
    
    # Compliance & Settings
    compliance_standards = models.JSONField(default=list)  # ['PEPPOL', 'GS1', etc.]
    timezone = models.CharField(max_length=50, default='Africa/Lagos')
    currency = models.CharField(max_length=3, default='NGN')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class CompanyUser(models.Model):
    """Extended User Profile for Multi-tenant"""
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrator'),
        ('MANAGER', 'Manager'),
        ('USER', 'User'),
        ('VIEWER', 'Viewer'),
    ]
    
    class Meta:
        db_table = 'company_users'
        indexes = [
            models.Index(fields=['company'], name='idx_user_company'),
            models.Index(fields=['user'], name='idx_user_ref'),
        ]
    
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    permissions = models.JSONField(blank=True, null=True)  # Role-based permissions
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name}"


# =============================================
# CORE REFERENCE TABLES
# =============================================

class DocumentType(models.Model):
    """EDI Document Types (850, 810, 820, etc.)"""
    
    DIRECTION_CHOICES = [
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),
        ('BOTH', 'Both'),
    ]
    
    FORMAT_CHOICES = [
        ('X12', 'ANSI X12'),
        ('EDIFACT', 'UN/EDIFACT'),
        ('XML', 'XML'),
        ('JSON', 'JSON'),
    ]
    
    class Meta:
        db_table = 'edi_document_types'
        
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10, unique=True)  # '850', '810', etc.
    name = models.CharField(max_length=100)  # 'Purchase Order', 'Invoice'
    description = models.TextField(blank=True, null=True)
    format_standard = models.CharField(max_length=20, choices=FORMAT_CHOICES, default='X12')
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='BOTH')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class TradingPartner(models.Model):
    """Trading Partners (Buyers, Sellers, etc.)"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('INACTIVE', 'Inactive'),
    ]
    
    PROTOCOL_CHOICES = [
        ('VAN', 'VAN (Value Added Network)'),
        ('AS2', 'AS2'),
        ('HTTPS', 'HTTPS'),
        ('SFTP', 'SFTP'),
        ('SCBN', 'Sterling Commerce Business Network'),
    ]
    
    class Meta:
        db_table = 'trading_partners'
        indexes = [
            models.Index(fields=['company'], name='idx_partner_comp'),
            models.Index(fields=['partner_code'], name='idx_partner_code'),
            models.Index(fields=['edi_id'], name='idx_partner_edi'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'partner_code'], 
                name='unique_company_partner_code'
            ),
        ]
        
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Basic Information
    name = models.CharField(max_length=255)
    partner_code = models.CharField(max_length=50)  # Internal reference
    edi_id = models.CharField(max_length=50)  # EDI partner ID (ISA qualifier)
    edi_qualifier = models.CharField(max_length=10)  # '01', '14', '16', etc.
    
    # Contact Information
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    
    # Address
    address = models.JSONField(blank=True, null=True)
    
    # Partner Configuration
    edi_formats_supported = models.JSONField(default=list)  # ['X12', 'EDIFACT']
    document_types_supported = models.JSONField(default=list)  # ['850', '810']
    communication_protocol = models.CharField(max_length=50, choices=PROTOCOL_CHOICES, default='SCBN')
    
    # Relationship Status
    partnership_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    onboarding_completed = models.BooleanField(default=False)
    
    # SLA & Performance
    sla_response_time_hours = models.IntegerField(blank=True, null=True)
    performance_metrics = models.JSONField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.partner_code} - {self.name}"


# =============================================
# EDI INTERCHANGE AND FUNCTIONAL GROUPS
# =============================================

class Interchange(models.Model):
    """EDI Interchange Headers (ISA/IEA)"""
    
    STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('PROCESSING', 'Processing'),
        ('PROCESSED', 'Processed'),
        ('ERROR', 'Error'),
        ('ACKNOWLEDGED', 'Acknowledged'),
    ]
    
    DIRECTION_CHOICES = [
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),
    ]
    
    class Meta:
        db_table = 'edi_interchanges'
        indexes = [
            models.Index(fields=['company'], name='idx_int_company'),
            models.Index(fields=['control_number'], name='idx_int_ctrl_num'),
            models.Index(fields=['interchange_date'], name='idx_int_date'),
            models.Index(fields=['status'], name='idx_int_status'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    control_number = models.CharField(max_length=20, unique=True)
    interchange_date = models.DateField()
    interchange_time = models.TimeField()
    
    sender_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='sent_interchanges'
    )
    receiver_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='received_interchanges'
    )
    
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    total_transactions = models.IntegerField(default=0)
    
    # File Information
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_size_bytes = models.IntegerField(blank=True, null=True)
    raw_content = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"ICN: {self.control_number}"


class FunctionalGroup(models.Model):
    """EDI Functional Groups (GS/GE)"""
    
    class Meta:
        db_table = 'edi_functional_groups'
        indexes = [
            models.Index(fields=['interchange'], name='idx_fg_interchange'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interchange = models.ForeignKey(Interchange, on_delete=models.CASCADE, related_name='functional_groups')
    group_control_number = models.CharField(max_length=20)
    functional_id_code = models.CharField(max_length=10)  # PO, IN, etc.
    application_senders_code = models.CharField(max_length=20)
    application_receivers_code = models.CharField(max_length=20)
    group_date = models.DateField()
    group_time = models.TimeField()
    transaction_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"GCN: {self.group_control_number}"


# =============================================
# MAIN EDI TRANSACTIONS TABLE
# =============================================

class EDITransaction(models.Model):
    """Main EDI Transactions Table"""
    
    STATUS_CHOICES = [
        ('RECEIVED', 'Received'),
        ('PROCESSING', 'Processing'),
        ('PARSED', 'Parsed'),
        ('ERROR', 'Error'),
        ('COMPLETED', 'Completed'),
        ('ACKNOWLEDGED', 'Acknowledged'),
    ]
    
    DIRECTION_CHOICES = [
        ('INBOUND', 'Inbound'),
        ('OUTBOUND', 'Outbound'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    VALIDATION_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VALID', 'Valid'),
        ('INVALID', 'Invalid'),
        ('WARNING', 'Warning'),
    ]
    
    class Meta:
        db_table = 'edi_transactions'
        indexes = [
            models.Index(fields=['company'], name='idx_trans_company'),
            models.Index(fields=['trading_partner'], name='idx_trans_partner'),
            models.Index(fields=['document_type'], name='idx_trans_doc_type'),
            models.Index(fields=['status'], name='idx_trans_status'),
            models.Index(fields=['direction'], name='idx_trans_direction'),
            models.Index(fields=['received_at'], name='idx_trans_received'),
            models.Index(fields=['po_number'], name='idx_trans_po_num'),
            models.Index(fields=['invoice_number'], name='idx_trans_inv_num'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    functional_group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE, blank=True, null=True)
    trading_partner = models.ForeignKey(TradingPartner, on_delete=models.PROTECT)
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT)
    
    # Transaction Identifiers
    transaction_control_number = models.CharField(max_length=50, blank=True, null=True)
    interchange_control_number = models.CharField(max_length=50, blank=True, null=True)
    group_control_number = models.CharField(max_length=50, blank=True, null=True)
    po_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Transaction Details
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RECEIVED')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    
    # File Information
    original_filename = models.CharField(max_length=255, blank=True, null=True)
    file_size_bytes = models.IntegerField(blank=True, null=True)
    file_format = models.CharField(max_length=20, blank=True, null=True)
    raw_content = models.TextField(blank=True, null=True)
    parsed_content = models.JSONField(blank=True, null=True)
    
    # AI Processing
    openai_summary = models.TextField(blank=True, null=True)
    openai_insights = models.JSONField(blank=True, null=True)
    validation_status = models.CharField(max_length=20, choices=VALIDATION_STATUS_CHOICES, default='PENDING')
    validation_errors = models.JSONField(blank=True, null=True)
    
    # Financial Information
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=3, default='NGN')
    line_item_count = models.IntegerField(blank=True, null=True)
    
    # Processing Timestamps
    received_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    tags = models.JSONField(default=list)  # For categorization
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.document_type.code} - {self.po_number or self.invoice_number or 'N/A'}"


class EDILineItem(models.Model):
    """EDI Line Items (For detailed transaction breakdown)"""
    
    class Meta:
        db_table = 'edi_line_items'
        indexes = [
            models.Index(fields=['transaction'], name='idx_line_trans'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction = models.ForeignKey(EDITransaction, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.CharField(max_length=20)
    
    # Product Information
    product_code = models.CharField(max_length=100, blank=True, null=True)
    product_description = models.TextField(blank=True, null=True)
    upc_code = models.CharField(max_length=50, blank=True, null=True)
    manufacturer_part_number = models.CharField(max_length=100, blank=True, null=True)
    buyer_part_number = models.CharField(max_length=100, blank=True, null=True)
    seller_part_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Quantity & Pricing
    quantity = models.DecimalField(max_digits=15, decimal_places=3, blank=True, null=True)
    unit_of_measure = models.CharField(max_length=10, default='EA')
    unit_price = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    extended_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    
    # Delivery Dates
    requested_delivery_date = models.DateField(blank=True, null=True)
    promised_delivery_date = models.DateField(blank=True, null=True)
    requested_ship_date = models.DateField(blank=True, null=True)
    
    # Additional Details
    line_item_data = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.transaction} - Line: {self.line_number}"


# =============================================
# LEGACY PURCHASE ORDER MODELS (For Compatibility)
# =============================================

class PurchaseOrder(models.Model):
    """Purchase Order Headers (850) - Legacy compatibility"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('ERROR', 'Error'),
    ]
    
    PO_TYPE_CHOICES = [
        ('SA', 'Stand-alone Order'),
        ('KN', 'Purchase Order Change Request'),
        ('NE', 'New Order'),
    ]
    
    class Meta:
        db_table = 'edi_purchase_orders'
        indexes = [
            models.Index(fields=['company'], name='idx_po_company'),
            models.Index(fields=['po_number'], name='idx_po_number'),
            models.Index(fields=['po_date'], name='idx_po_date'),
            models.Index(fields=['buyer_partner'], name='idx_po_buyer'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    edi_transaction = models.OneToOneField(EDITransaction, on_delete=models.CASCADE, blank=True, null=True)
    functional_group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE)
    
    po_number = models.CharField(max_length=50)
    po_date = models.DateField()
    po_type = models.CharField(max_length=10, choices=PO_TYPE_CHOICES, default='SA')
    
    buyer_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='purchase_orders_as_buyer'
    )
    seller_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='purchase_orders_as_seller'
    )
    
    # Ship To Information
    ship_to_name = models.CharField(max_length=200, blank=True, null=True)
    ship_to_address = models.JSONField(blank=True, null=True)
    
    # Dates
    requested_ship_date = models.DateField(blank=True, null=True)
    requested_delivery_date = models.DateField(blank=True, null=True)
    
    # Financial
    currency_code = models.CharField(max_length=3, default='USD')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_terms = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO: {self.po_number}"


# =============================================
# SCBN INTEGRATION & WORKFLOW
# =============================================

class SCBNIntegrationLog(models.Model):
    """SCBN Integration Log"""
    
    OPERATION_CHOICES = [
        ('POLL', 'Poll'),
        ('SEND', 'Send'),
        ('RECEIVE', 'Receive'),
        ('AUTHENTICATE', 'Authenticate'),
    ]
    
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('FAILURE', 'Failure'),
        ('WARNING', 'Warning'),
    ]
    
    class Meta:
        db_table = 'scbn_integration_log'
        indexes = [
            models.Index(fields=['company'], name='idx_scbn_company'),
            models.Index(fields=['started_at'], name='idx_scbn_started'),
        ]
    
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    operation_type = models.CharField(max_length=50, choices=OPERATION_CHOICES)
    operation_status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    
    request_data = models.JSONField(blank=True, null=True)
    response_data = models.JSONField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    response_time_ms = models.IntegerField(blank=True, null=True)
    
    files_processed = models.IntegerField(default=0)
    files_failed = models.IntegerField(default=0)
    
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.company.name} - {self.operation_type} - {self.operation_status}"


# =============================================
# ANALYTICS & REPORTING
# =============================================

class MonthlyTransactionSummary(models.Model):
    """Monthly Transaction Summary (For Performance)"""
    
    class Meta:
        db_table = 'monthly_transaction_summary'
        indexes = [
            models.Index(fields=['company', 'year', 'month'], name='idx_monthly_comp_date'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'trading_partner', 'document_type', 'year', 'month'],
                name='unique_monthly_summary'
            ),
        ]
    
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    trading_partner = models.ForeignKey(TradingPartner, on_delete=models.CASCADE, blank=True, null=True)
    document_type = models.ForeignKey(DocumentType, on_delete=models.CASCADE, blank=True, null=True)
    
    year = models.IntegerField()
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    # Volume Metrics
    transaction_count = models.IntegerField(default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_processing_time_seconds = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Quality Metrics
    success_rate = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    error_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.company.name} - {self.year}/{self.month:02d}"


class DailyAnalytics(models.Model):
    """Daily Analytics (For Real-time Dashboards)"""
    
    class Meta:
        db_table = 'daily_analytics'
        indexes = [
            models.Index(fields=['company', 'analytics_date'], name='idx_daily_comp_date'),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'analytics_date'],
                name='unique_daily_analytics'
            ),
        ]
    
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    analytics_date = models.DateField()
    
    # Transaction Metrics
    total_transactions = models.IntegerField(default=0)
    inbound_transactions = models.IntegerField(default=0)
    outbound_transactions = models.IntegerField(default=0)
    failed_transactions = models.IntegerField(default=0)
    
    # Financial Metrics
    total_transaction_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_transaction_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Performance Metrics
    avg_processing_time_minutes = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    system_uptime_percentage = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    
    # Partner Activity
    active_partners_count = models.IntegerField(default=0)
    new_partners_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.company.name} - {self.analytics_date}"


# =============================================
# AUDIT AND ERROR HANDLING
# =============================================

class ProcessingError(models.Model):
    """EDI Processing Errors"""
    
    SEVERITY_CHOICES = [
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
        ('FATAL', 'Fatal'),
        ('INFO', 'Info'),
    ]
    
    class Meta:
        db_table = 'edi_processing_errors'
        indexes = [
            models.Index(fields=['company'], name='idx_err_company'),
            models.Index(fields=['interchange'], name='idx_err_interchange'),
            models.Index(fields=['severity'], name='idx_err_severity'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    interchange = models.ForeignKey(Interchange, on_delete=models.CASCADE, blank=True, null=True)
    edi_transaction = models.ForeignKey(EDITransaction, on_delete=models.CASCADE, blank=True, null=True)
    
    transaction_type = models.CharField(max_length=10, blank=True, null=True)
    error_code = models.CharField(max_length=20, blank=True, null=True)
    error_description = models.TextField()
    error_location = models.CharField(max_length=100, blank=True, null=True)  # Which segment/element
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Error: {self.error_code} - {self.severity}"


class ProcessingLog(models.Model):
    """EDI Processing Log"""
    
    STATUS_CHOICES = [
        ('STARTED', 'Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('SKIPPED', 'Skipped'),
    ]
    
    class Meta:
        db_table = 'edi_processing_log'
        indexes = [
            models.Index(fields=['company'], name='idx_log_company'),
            models.Index(fields=['interchange'], name='idx_log_interchange'),
            models.Index(fields=['created_at'], name='idx_log_created'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    interchange = models.ForeignKey(Interchange, on_delete=models.CASCADE, blank=True, null=True)
    edi_transaction = models.ForeignKey(EDITransaction, on_delete=models.CASCADE, blank=True, null=True)
    
    process_step = models.CharField(max_length=50)
    process_status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    process_message = models.TextField(blank=True, null=True)
    processing_duration = models.DurationField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Log: {self.process_step} - {self.process_status}"


# =============================================
# INVOICE TRANSACTIONS (810) - Legacy Compatibility
# =============================================

class Invoice(models.Model):
    """Invoice Headers (810) - Legacy compatibility"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent'),
        ('RECEIVED', 'Received'),
        ('PAID', 'Paid'),
        ('DISPUTED', 'Disputed'),
        ('CANCELLED', 'Cancelled'),
        ('ERROR', 'Error'),
    ]
    
    class Meta:
        db_table = 'edi_invoices'
        indexes = [
            models.Index(fields=['company'], name='idx_inv_company'),
            models.Index(fields=['invoice_number'], name='idx_inv_number'),
            models.Index(fields=['invoice_date'], name='idx_inv_date'),
            models.Index(fields=['purchase_order'], name='idx_inv_po'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    edi_transaction = models.OneToOneField(EDITransaction, on_delete=models.CASCADE, blank=True, null=True)
    functional_group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE)
    
    invoice_number = models.CharField(max_length=50)
    invoice_date = models.DateField()
    
    # Related PO (optional)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, blank=True, null=True)
    
    seller_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='invoices_as_seller'
    )
    buyer_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='invoices_as_buyer'
    )
    
    # Financial Information
    subtotal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Payment Information
    currency_code = models.CharField(max_length=3, default='USD')
    payment_terms = models.CharField(max_length=50, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Invoice: {self.invoice_number}"


# =============================================
# PAYMENT TRANSACTIONS (820) - Legacy Compatibility
# =============================================

class Payment(models.Model):
    """Payment Headers (820) - Legacy compatibility"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSED', 'Processed'),
        ('CLEARED', 'Cleared'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('ACH', 'ACH'),
        ('CHECK', 'Check'),
        ('WIRE', 'Wire'),
        ('CARD', 'Credit/Debit Card'),
    ]
    
    class Meta:
        db_table = 'edi_payments'
        indexes = [
            models.Index(fields=['company'], name='idx_pay_company'),
            models.Index(fields=['payment_number'], name='idx_pay_number'),
            models.Index(fields=['payment_date'], name='idx_pay_date'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    edi_transaction = models.OneToOneField(EDITransaction, on_delete=models.CASCADE, blank=True, null=True)
    functional_group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE)
    
    payment_number = models.CharField(max_length=50)
    payment_date = models.DateField()
    
    payer_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='payments_as_payer',
        blank=True, null=True
    )
    payee_partner = models.ForeignKey(
        TradingPartner, 
        on_delete=models.PROTECT,
        related_name='payments_as_payee',
        blank=True, null=True
    )
    
    # Payment Details
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, default='ACH')
    currency_code = models.CharField(max_length=3, default='USD')
    
    # Banking Information
    bank_account_number = models.CharField(max_length=50, blank=True, null=True)
    routing_number = models.CharField(max_length=20, blank=True, null=True)
    check_number = models.CharField(max_length=20, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment: {self.payment_number}"


class PaymentDetail(models.Model):
    """Payment Details (which invoices are being paid)"""
    
    class Meta:
        db_table = 'edi_payment_details'
        indexes = [
            models.Index(fields=['payment'], name='idx_paydet_payment'),
            models.Index(fields=['invoice'], name='idx_paydet_invoice'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='payment_details')
    
    # Invoice being paid
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, blank=True, null=True)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Payment allocation
    payment_amount = models.DecimalField(max_digits=15, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    adjustment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Payment: {self.payment.payment_number} - Invoice: {self.invoice_number}"


# =============================================
# DOCUMENT WORKFLOW & APPROVAL SYSTEM
# =============================================

class DocumentWorkflow(models.Model):
    """Document Workflow States"""
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('ON_HOLD', 'On Hold'),
    ]
    
    class Meta:
        db_table = 'document_workflows'
        indexes = [
            models.Index(fields=['company'], name='idx_wf_company'),
            models.Index(fields=['edi_transaction'], name='idx_wf_transaction'),
            models.Index(fields=['workflow_status'], name='idx_wf_status'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    edi_transaction = models.ForeignKey(EDITransaction, on_delete=models.CASCADE)
    
    # Workflow Information
    workflow_name = models.CharField(max_length=100)
    current_step = models.CharField(max_length=100)
    workflow_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    
    # Approval Process
    requires_approval = models.BooleanField(default=False)
    approved_by = models.ForeignKey(CompanyUser, on_delete=models.PROTECT, blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approval_notes = models.TextField(blank=True, null=True)
    
    # Automation
    is_automated = models.BooleanField(default=False)
    automation_rules = models.JSONField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.workflow_name} - {self.current_step}"


# =============================================
# SYSTEM CONFIGURATION & API USAGE
# =============================================

class SystemConfig(models.Model):
    """System Configuration"""
    
    class Meta:
        db_table = 'system_config'
    
    id = models.AutoField(primary_key=True)
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.JSONField()
    description = models.TextField(blank=True, null=True)
    is_editable = models.BooleanField(default=True)
    updated_by = models.ForeignKey(CompanyUser, on_delete=models.PROTECT, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.config_key


class APIUsageLog(models.Model):
    """API Usage Tracking"""
    
    class Meta:
        db_table = 'api_usage_log'
        indexes = [
            models.Index(fields=['company'], name='idx_api_company'),
            models.Index(fields=['created_at'], name='idx_api_created'),
            models.Index(fields=['endpoint'], name='idx_api_endpoint'),
        ]
    
    id = models.AutoField(primary_key=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL, blank=True, null=True)
    
    # API Details
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    status_code = models.IntegerField()
    response_time_ms = models.IntegerField(blank=True, null=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    request_size_bytes = models.IntegerField(blank=True, null=True)
    response_size_bytes = models.IntegerField(blank=True, null=True)
    
    # Rate Limiting
    rate_limit_remaining = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"


class SLAMonitoring(models.Model):
    """SLA Monitoring (Enterprise Feature)"""
    
    MEASUREMENT_PERIOD_CHOICES = [
        ('HOURLY', 'Hourly'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
    ]
    
    class Meta:
        db_table = 'sla_monitoring'
        indexes = [
            models.Index(fields=['company'], name='idx_sla_company'),
            models.Index(fields=['trading_partner'], name='idx_sla_partner'),
            models.Index(fields=['measured_at'], name='idx_sla_measured'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    trading_partner = models.ForeignKey(TradingPartner, on_delete=models.CASCADE)
    
    # SLA Metrics
    metric_name = models.CharField(max_length=100)  # 'response_time', 'uptime', 'error_rate'
    target_value = models.DecimalField(max_digits=10, decimal_places=2)
    actual_value = models.DecimalField(max_digits=10, decimal_places=2)
    measurement_period = models.CharField(max_length=20, choices=MEASUREMENT_PERIOD_CHOICES)
    
    # Alert Configuration
    alert_threshold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    alert_sent = models.BooleanField(default=False)
    alert_sent_at = models.DateTimeField(blank=True, null=True)
    
    measured_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.company.name} - {self.metric_name}: {self.actual_value}"


# =============================================
# CUSTOM REPORTS (Enterprise Feature)
# =============================================

class CustomReport(models.Model):
    """Custom Reports (Enterprise Feature)"""
    
    REPORT_TYPE_CHOICES = [
        ('TRANSACTION_SUMMARY', 'Transaction Summary'),
        ('PARTNER_PERFORMANCE', 'Partner Performance'),
        ('FINANCIAL', 'Financial Report'),
        ('COMPLIANCE', 'Compliance Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    FREQUENCY_CHOICES = [
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('YEARLY', 'Yearly'),
    ]
    
    OUTPUT_FORMAT_CHOICES = [
        ('JSON', 'JSON'),
        ('CSV', 'CSV'),
        ('PDF', 'PDF'),
        ('EXCEL', 'Excel'),
    ]
    
    class Meta:
        db_table = 'custom_reports'
        indexes = [
            models.Index(fields=['company'], name='idx_report_company'),
            models.Index(fields=['created_by'], name='idx_report_creator'),
            models.Index(fields=['next_run_date'], name='idx_report_next_run'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    created_by = models.ForeignKey(CompanyUser, on_delete=models.PROTECT)
    
    # Report Configuration
    report_name = models.CharField(max_length=255)
    report_description = models.TextField(blank=True, null=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    
    # Report Parameters
    filters = models.JSONField(blank=True, null=True)  # Date ranges, partners, document types
    grouping = models.JSONField(blank=True, null=True)  # How to group the data
    metrics = models.JSONField(blank=True, null=True)  # What metrics to include
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, blank=True, null=True)
    next_run_date = models.DateTimeField(blank=True, null=True)
    
    # Report Settings
    output_format = models.CharField(max_length=20, choices=OUTPUT_FORMAT_CHOICES, default='JSON')
    recipients = models.JSONField(default=list)  # Email addresses for automated reports
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.report_name} - {self.company.name}"