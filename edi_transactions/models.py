from django.db import models
import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
# Create your models here.



# =============================================
# CORE REFERENCE TABLES
# =============================================

class DocumentType(models.Model):
    """EDI Document Types (850, 810, 820, etc.)"""
    
    class Meta:
        db_table = 'edi_core_document_types'
        
    document_type_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_set_code = models.CharField(max_length=10, unique=True)
    document_name = models.CharField(max_length=100)
    document_description = models.TextField(blank=True, null=True)
    is_inbound = models.BooleanField(default=True)
    is_outbound = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.transaction_set_code} - {self.document_name}"


class TradingPartner(models.Model):
    """Trading Partners (Buyers, Sellers, etc.)"""
    
    class Meta:
        db_table = 'edi_core_trading_partners'
        indexes = [
            models.Index(fields=['partner_code'], name='idx_trading_partners_code'),
            models.Index(fields=['edi_id'], name='idx_trading_partners_edi_id'),
        ]
        
    partner_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    partner_code = models.CharField(max_length=20, unique=True)
    company_name = models.CharField(max_length=200)
    edi_id = models.CharField(max_length=50, unique=True)
    qualifier = models.CharField(max_length=10)  # 01=DUNS, 12=Phone, etc.
    
    # Contact Information
    contact_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Address
    address_line1 = models.CharField(max_length=100, blank=True, null=True)
    address_line2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=10, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=5, default='US')
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.partner_code} - {self.company_name}"


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
        db_table = 'edi_transactions_interchanges'
        indexes = [
            models.Index(fields=['interchange_control_number'], name='idx_interchanges_control_number'),
            models.Index(fields=['interchange_date'], name='idx_interchanges_date'),
            models.Index(fields=['status'], name='idx_interchanges_status'),
        ]
    
    interchange_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interchange_control_number = models.CharField(max_length=20, unique=True)
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
    
    created_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"ICN: {self.interchange_control_number}"


class FunctionalGroup(models.Model):
    """EDI Functional Groups (GS/GE)"""
    
    class Meta:
        db_table = 'edi_transactions_functional_groups'
    
    group_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interchange = models.ForeignKey(Interchange, on_delete=models.CASCADE)
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
# PURCHASE ORDER TRANSACTIONS (850)
# =============================================

class PurchaseOrder(models.Model):
    """Purchase Order Headers (850)"""
    
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
        db_table = 'edi_transactions_purchase_orders'
        indexes = [
            models.Index(fields=['po_number'], name='idx_po_number'),
            models.Index(fields=['po_date'], name='idx_po_date'),
            models.Index(fields=['buyer_partner'], name='idx_po_buyer'),
            models.Index(fields=['status'], name='idx_po_status'),
        ]
    
    po_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE)
    transaction_control_number = models.CharField(max_length=20)
    
    po_number = models.CharField(max_length=50, unique=True)
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
    ship_to_address1 = models.CharField(max_length=100, blank=True, null=True)
    ship_to_address2 = models.CharField(max_length=100, blank=True, null=True)
    ship_to_city = models.CharField(max_length=50, blank=True, null=True)
    ship_to_state = models.CharField(max_length=10, blank=True, null=True)
    ship_to_postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Dates
    requested_ship_date = models.DateField(blank=True, null=True)
    requested_delivery_date = models.DateField(blank=True, null=True)
    
    # Financial
    currency_code = models.CharField(max_length=3, default='USD')
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Payment Terms
    payment_terms = models.CharField(max_length=50, blank=True, null=True)  # NET30, 2/10NET30
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO: {self.po_number}"


class POLineItem(models.Model):
    """Purchase Order Line Items"""
    
    class Meta:
        db_table = 'edi_transactions_po_line_items'
    
    line_item_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.CharField(max_length=20)
    
    # Item Information
    item_number = models.CharField(max_length=100, blank=True, null=True)
    item_description = models.TextField(blank=True, null=True)
    buyer_part_number = models.CharField(max_length=100, blank=True, null=True)
    seller_part_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Quantity and Pricing
    quantity_ordered = models.DecimalField(max_digits=12, decimal_places=3)
    unit_of_measure = models.CharField(max_length=10, default='EA')
    unit_price = models.DecimalField(max_digits=10, decimal_places=4)
    extended_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Delivery
    requested_ship_date = models.DateField(blank=True, null=True)
    requested_delivery_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"PO: {self.purchase_order.po_number} - Line: {self.line_number}"


# =============================================
# INVOICE TRANSACTIONS (810)
# =============================================

class Invoice(models.Model):
    """Invoice Headers (810)"""
    
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
        db_table = 'edi_transactions_invoices'
        indexes = [
            models.Index(fields=['invoice_number'], name='idx_invoice_number'),
            models.Index(fields=['invoice_date'], name='idx_invoice_date'),
            models.Index(fields=['po'], name='idx_invoice_po_id'),
            models.Index(fields=['status'], name='idx_invoice_status'),
        ]
    
    invoice_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE)
    transaction_control_number = models.CharField(max_length=20)
    
    invoice_number = models.CharField(max_length=50, unique=True)
    invoice_date = models.DateField()
    
    # Related PO (optional for some invoices)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, blank=True, null=True)
    
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


class InvoiceLineItem(models.Model):
    """Invoice Line Items"""
    
    class Meta:
        db_table = 'edi_transactions_invoice_line_items'
    
    invoice_line_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    line_number = models.CharField(max_length=20)
    
    # Reference to PO Line Item (if applicable)
    po_line_item = models.ForeignKey(POLineItem, on_delete=models.PROTECT, blank=True, null=True)
    
    # Item Information
    item_number = models.CharField(max_length=100, blank=True, null=True)
    item_description = models.TextField(blank=True, null=True)
    
    # Quantity and Pricing
    quantity_invoiced = models.DecimalField(max_digits=12, decimal_places=3)
    unit_of_measure = models.CharField(max_length=10, default='EA')
    unit_price = models.DecimalField(max_digits=10, decimal_places=4)
    extended_amount = models.DecimalField(max_digits=15, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Invoice: {self.invoice.invoice_number} - Line: {self.line_number}"


# =============================================
# PAYMENT TRANSACTIONS (820)
# =============================================

class Payment(models.Model):
    """Payment Headers (820)"""
    
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
    ]
    
    class Meta:
        db_table = 'edi_transactions_payments'
        indexes = [
            models.Index(fields=['payment_number'], name='idx_payment_number'),
            models.Index(fields=['payment_date'], name='idx_payment_date'),
            models.Index(fields=['status'], name='idx_payment_status'),
        ]
    
    payment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(FunctionalGroup, on_delete=models.CASCADE)
    transaction_control_number = models.CharField(max_length=20)
    
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
        db_table = 'edi_transactions_payment_details'
    
    payment_detail_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
# AUDIT AND ERROR HANDLING
# =============================================

class ProcessingError(models.Model):
    """EDI Processing Errors"""
    
    SEVERITY_CHOICES = [
        ('ERROR', 'Error'),
        ('WARNING', 'Warning'),
        ('FATAL', 'Fatal'),
    ]
    
    class Meta:
        db_table = 'edi_audit_processing_errors'
    
    error_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interchange = models.ForeignKey(Interchange, on_delete=models.CASCADE, blank=True, null=True)
    
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
    
    class Meta:
        db_table = 'edi_audit_processing_log'
    
    log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interchange = models.ForeignKey(Interchange, on_delete=models.CASCADE, blank=True, null=True)
    
    process_step = models.CharField(max_length=50)
    process_status = models.CharField(max_length=20)
    process_message = models.TextField(blank=True, null=True)
    processing_duration = models.DurationField(blank=True, null=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Log: {self.process_step} - {self.process_status}"