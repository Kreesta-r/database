from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json
from .models import (
    # Core tenant models
    SubscriptionPlan, Company, CompanyUser,
    
    # Reference models
    DocumentType, TradingPartner,
    
    # EDI transaction models
    Interchange, FunctionalGroup, EDITransaction, EDILineItem,
    
    # Legacy compatibility models
    PurchaseOrder, Invoice, Payment, PaymentDetail,
    
    # Integration & workflow
    SCBNIntegrationLog, DocumentWorkflow,
    
    # Analytics models
    MonthlyTransactionSummary, DailyAnalytics,
    
    # Audit & error handling
    ProcessingError, ProcessingLog,
    
    # System configuration
    SystemConfig, APIUsageLog, SLAMonitoring, CustomReport
)


# ==============================================
# CORE TENANT & SUBSCRIPTION ADMIN
# ==============================================

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'price_ngn', 'max_users', 'max_transactions_monthly', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'display_name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'subscription_plan', 'subscription_status', 'company_size', 'is_active', 'created_at')
    list_filter = ('subscription_plan', 'subscription_status', 'company_size', 'is_active', 'industry')
    search_fields = ('name', 'email', 'registration_number', 'scbn_mailbox_id')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'registration_number', 'tax_id', 'email', 'phone', 'website', 'industry', 'company_size')
        }),
        ('Address', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_status', 'subscription_start_date', 'subscription_end_date')
        }),
        ('SCBN Integration', {
            'fields': ('scbn_mailbox_id', 'scbn_credentials'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('compliance_standards', 'company_timezone', 'currency', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'role', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'company__subscription_plan')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'company__name')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company')


# ==============================================
# REFERENCE MODELS ADMIN
# ==============================================

@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'format_standard', 'direction', 'is_active')
    list_filter = ('format_standard', 'direction', 'is_active')
    search_fields = ('code', 'name', 'description')
    readonly_fields = ('created_at',)


@admin.register(TradingPartner)
class TradingPartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'partner_code', 'edi_id', 'partnership_status', 'onboarding_completed', 'is_active')
    list_filter = ('partnership_status', 'onboarding_completed', 'is_active', 'communication_protocol')
    search_fields = ('name', 'partner_code', 'edi_id', 'company__name', 'contact_email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'name', 'partner_code', 'edi_id', 'edi_qualifier')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email', 'contact_phone', 'address'),
            'classes': ('collapse',)
        }),
        ('Configuration', {
            'fields': ('edi_formats_supported', 'document_types_supported', 'communication_protocol')
        }),
        ('Status', {
            'fields': ('partnership_status', 'onboarding_completed', 'is_active')
        }),
        ('SLA & Performance', {
            'fields': ('sla_response_time_hours', 'performance_metrics'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


# ==============================================
# EDI TRANSACTION ADMIN
# ==============================================

class EDILineItemInline(admin.TabularInline):
    model = EDILineItem
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('line_number', 'product_code', 'product_description', 'quantity', 'unit_price', 'extended_price')


@admin.register(Interchange)
class InterchangeAdmin(admin.ModelAdmin):
    list_display = ('control_number', 'company', 'direction', 'status', 'total_transactions', 'interchange_date', 'created_at')
    list_filter = ('direction', 'status', 'interchange_date', 'created_at')
    search_fields = ('control_number', 'company__name', 'sender_partner__name', 'receiver_partner__name')
    readonly_fields = ('created_at', 'processed_at')
    date_hierarchy = 'interchange_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'sender_partner', 'receiver_partner')


@admin.register(FunctionalGroup)
class FunctionalGroupAdmin(admin.ModelAdmin):
    list_display = ('group_control_number', 'functional_id_code', 'interchange', 'transaction_count', 'group_date')
    list_filter = ('functional_id_code', 'group_date')
    search_fields = ('group_control_number', 'application_senders_code', 'application_receivers_code')
    readonly_fields = ('created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('interchange')


@admin.register(EDITransaction)
class EDITransactionAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'company', 'trading_partner', 'direction', 'status', 'po_number', 'invoice_number', 'total_amount', 'received_at')
    list_filter = ('direction', 'status', 'priority', 'validation_status', 'document_type', 'received_at')
    search_fields = ('po_number', 'invoice_number', 'transaction_control_number', 'company__name', 'trading_partner__name')
    readonly_fields = ('created_at', 'updated_at', 'received_at', 'processed_at', 'completed_at')
    date_hierarchy = 'received_at'
    inlines = [EDILineItemInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'trading_partner', 'document_type', 'direction', 'status', 'priority')
        }),
        ('Transaction Identifiers', {
            'fields': ('transaction_control_number', 'interchange_control_number', 'group_control_number', 'po_number', 'invoice_number')
        }),
        ('File Information', {
            'fields': ('original_filename', 'file_size_bytes', 'file_format'),
            'classes': ('collapse',)
        }),
        ('AI Processing', {
            'fields': ('openai_summary', 'validation_status', 'validation_errors'),
            'classes': ('collapse',)
        }),
        ('Financial', {
            'fields': ('total_amount', 'currency', 'line_item_count')
        }),
        ('Processing Timeline', {
            'fields': ('received_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'trading_partner', 'document_type')


# ==============================================
# LEGACY COMPATIBILITY ADMIN
# ==============================================

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'company', 'buyer_partner', 'seller_partner', 'po_date', 'total_amount', 'status')
    list_filter = ('status', 'po_type', 'po_date', 'created_at')
    search_fields = ('po_number', 'company__name', 'buyer_partner__name', 'seller_partner__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'po_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'buyer_partner', 'seller_partner')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'company', 'seller_partner', 'buyer_partner', 'invoice_date', 'total_amount', 'status')
    list_filter = ('status', 'invoice_date', 'created_at')
    search_fields = ('invoice_number', 'company__name', 'seller_partner__name', 'buyer_partner__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'invoice_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'seller_partner', 'buyer_partner', 'purchase_order')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'company', 'payer_partner', 'payee_partner', 'payment_date', 'payment_amount', 'status')
    list_filter = ('status', 'payment_method', 'payment_date')
    search_fields = ('payment_number', 'company__name', 'payer_partner__name', 'payee_partner__name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'payment_date'


# ==============================================
# INTEGRATION & WORKFLOW ADMIN
# ==============================================

@admin.register(SCBNIntegrationLog)
class SCBNIntegrationLogAdmin(admin.ModelAdmin):
    list_display = ('company', 'operation_type', 'operation_status', 'files_processed', 'files_failed', 'response_time_ms', 'started_at')
    list_filter = ('operation_type', 'operation_status', 'started_at')
    search_fields = ('company__name',)
    readonly_fields = ('started_at', 'completed_at', 'created_at')
    date_hierarchy = 'started_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


@admin.register(DocumentWorkflow)
class DocumentWorkflowAdmin(admin.ModelAdmin):
    list_display = ('workflow_name', 'company', 'edi_transaction', 'current_step', 'workflow_status', 'requires_approval', 'is_automated')
    list_filter = ('workflow_status', 'requires_approval', 'is_automated', 'created_at')
    search_fields = ('workflow_name', 'company__name')
    readonly_fields = ('created_at', 'updated_at', 'approved_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'edi_transaction', 'approved_by')


# ==============================================
# ANALYTICS ADMIN
# ==============================================

@admin.register(MonthlyTransactionSummary)
class MonthlyTransactionSummaryAdmin(admin.ModelAdmin):
    list_display = ('company', 'year', 'month', 'transaction_count', 'total_amount', 'success_rate', 'error_count')
    list_filter = ('year', 'month', 'company', 'document_type')
    search_fields = ('company__name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'trading_partner', 'document_type')


@admin.register(DailyAnalytics)
class DailyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('company', 'analytics_date', 'total_transactions', 'total_transaction_value', 'active_partners_count', 'system_uptime_percentage')
    list_filter = ('analytics_date', 'company')
    search_fields = ('company__name',)
    readonly_fields = ('created_at',)
    date_hierarchy = 'analytics_date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company')


# ==============================================
# AUDIT & ERROR HANDLING ADMIN
# ==============================================

@admin.register(ProcessingError)
class ProcessingErrorAdmin(admin.ModelAdmin):
    list_display = ('error_code', 'company', 'severity', 'transaction_type', 'error_description_short', 'created_at')
    list_filter = ('severity', 'transaction_type', 'created_at')
    search_fields = ('error_code', 'error_description', 'company__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def error_description_short(self, obj):
        return obj.error_description[:50] + '...' if len(obj.error_description) > 50 else obj.error_description
    error_description_short.short_description = 'Error Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'interchange', 'edi_transaction')


@admin.register(ProcessingLog)
class ProcessingLogAdmin(admin.ModelAdmin):
    list_display = ('process_step', 'company', 'process_status', 'processing_duration', 'created_at')
    list_filter = ('process_status', 'process_step', 'created_at')
    search_fields = ('process_step', 'process_message', 'company__name')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'interchange', 'edi_transaction')


# ==============================================
# SYSTEM CONFIGURATION ADMIN
# ==============================================

@admin.register(SystemConfig)
class SystemConfigAdmin(admin.ModelAdmin):
    list_display = ('config_key', 'config_value_short', 'is_editable', 'updated_at')
    list_filter = ('is_editable', 'updated_at')
    search_fields = ('config_key', 'description')
    readonly_fields = ('updated_at',)
    
    def config_value_short(self, obj):
        value_str = str(obj.config_value)
        return value_str[:50] + '...' if len(value_str) > 50 else value_str
    config_value_short.short_description = 'Config Value'


@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('endpoint', 'method', 'company', 'status_code', 'response_time_ms', 'created_at')
    list_filter = ('method', 'status_code', 'created_at')
    search_fields = ('endpoint', 'company__name', 'ip_address')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'user')


@admin.register(SLAMonitoring)
class SLAMonitoringAdmin(admin.ModelAdmin):
    list_display = ('company', 'trading_partner', 'metric_name', 'target_value', 'actual_value', 'measurement_period', 'alert_sent', 'measured_at')
    list_filter = ('metric_name', 'measurement_period', 'alert_sent', 'measured_at')
    search_fields = ('company__name', 'trading_partner__name', 'metric_name')
    readonly_fields = ('created_at', 'measured_at', 'alert_sent_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'trading_partner')


@admin.register(CustomReport)
class CustomReportAdmin(admin.ModelAdmin):
    list_display = ('report_name', 'company', 'report_type', 'is_scheduled', 'schedule_frequency', 'is_active', 'next_run_date')
    list_filter = ('report_type', 'is_scheduled', 'schedule_frequency', 'is_active', 'created_at')
    search_fields = ('report_name', 'company__name', 'report_description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'created_by', 'report_name', 'report_description', 'report_type')
        }),
        ('Report Configuration', {
            'fields': ('filters', 'grouping', 'metrics'),
            'classes': ('collapse',)
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency', 'next_run_date')
        }),
        ('Output Settings', {
            'fields': ('output_format', 'recipients', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('company', 'created_by')


# ==============================================
# CUSTOM ADMIN ACTIONS
# ==============================================

def mark_transactions_as_processed(modeladmin, request, queryset):
    queryset.update(status='PROCESSED')
mark_transactions_as_processed.short_description = "Mark selected transactions as processed"

def retry_failed_transactions(modeladmin, request, queryset):
    queryset.filter(status='ERROR').update(status='RECEIVED')
retry_failed_transactions.short_description = "Retry failed transactions"

# Add custom actions to EDITransaction admin
EDITransactionAdmin.actions = [mark_transactions_as_processed, retry_failed_transactions]


# ==============================================
# ADMIN SITE CUSTOMIZATION
# ==============================================

admin.site.site_header = 'OH-Res EDI Platform Administration'
admin.site.site_title = 'OH-Res EDI Admin'
admin.site.index_title = 'Welcome to OH-Res EDI Platform Administration'