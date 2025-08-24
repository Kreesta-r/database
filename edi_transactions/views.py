from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    Company, CompanyUser, SubscriptionPlan,
    TradingPartner, PurchaseOrder, Invoice, Payment,
    DocumentType, EDITransaction, Interchange, FunctionalGroup,
    MonthlyTransactionSummary, DailyAnalytics, CustomReport,
    SystemConfig, APIUsageLog, SCBNIntegrationLog,
    ProcessingError, ProcessingLog
)

# ---------------------------
# Authentication Views
# ---------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "auth/login.html", {"error": "Invalid credentials"})
    return render(request, "auth/login.html")

@login_required
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    company = request.user.companyuser.company
    total_partners = TradingPartner.objects.filter(company=company).count()
    total_transactions = EDITransaction.objects.filter(company=company).count()
    recent_transactions = EDITransaction.objects.filter(company=company).order_by("-created_at")[:5]
    
    return render(request, "dashboard.html", {
        "company": company,
        "total_partners": total_partners,
        "total_transactions": total_transactions,
        "recent_transactions": recent_transactions,
    })

# ---------------------------
# Company & Subscription
# ---------------------------
@login_required
def company_detail(request):
    company = request.user.companyuser.company
    return render(request, "company/detail.html", {"company": company})

@login_required
def subscription_plans(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, "company/plans.html", {"plans": plans})

# ---------------------------
# Trading Partners
# ---------------------------
@login_required
def partner_list(request):
    company = request.user.companyuser.company
    partners = TradingPartner.objects.filter(company=company)
    paginator = Paginator(partners, 10)
    page = request.GET.get("page")
    partners_page = paginator.get_page(page)
    return render(request, "partners/list.html", {"partners": partners_page})

@login_required
def partner_detail(request, partner_id):
    partner = get_object_or_404(TradingPartner, id=partner_id, company=request.user.companyuser.company)
    return render(request, "partners/detail.html", {"partner": partner})

@login_required
def partner_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        TradingPartner.objects.create(company=request.user.companyuser.company, name=name)
        return redirect("partner_list")
    return render(request, "partners/create.html")

@login_required
def partner_edit(request, partner_id):
    partner = get_object_or_404(TradingPartner, id=partner_id, company=request.user.companyuser.company)
    if request.method == "POST":
        partner.name = request.POST.get("name")
        partner.save()
        return redirect("partner_detail", partner_id=partner.id)
    return render(request, "partners/edit.html", {"partner": partner})

@login_required
def partner_delete(request, partner_id):
    partner = get_object_or_404(TradingPartner, id=partner_id, company=request.user.companyuser.company)
    partner.delete()
    return redirect("partner_list")

# ---------------------------
# Purchase Orders
# ---------------------------
@login_required
def purchase_order_list(request):
    company = request.user.companyuser.company
    pos = PurchaseOrder.objects.filter(company=company)
    return render(request, "orders/list.html", {"orders": pos})

@login_required
def purchase_order_detail(request, order_id):
    order = get_object_or_404(PurchaseOrder, id=order_id, company=request.user.companyuser.company)
    return render(request, "orders/detail.html", {"order": order})

# ---------------------------
# Invoices
# ---------------------------
@login_required
def invoice_list(request):
    company = request.user.companyuser.company
    invoices = Invoice.objects.filter(company=company)
    return render(request, "invoices/list.html", {"invoices": invoices})

@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, company=request.user.companyuser.company)
    return render(request, "invoices/detail.html", {"invoice": invoice})

# ---------------------------
# Payments
# ---------------------------
@login_required
def payment_list(request):
    company = request.user.companyuser.company
    payments = Payment.objects.filter(company=company)
    return render(request, "payments/list.html", {"payments": payments})

@login_required
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, company=request.user.companyuser.company)
    return render(request, "payments/detail.html", {"payment": payment})

# ---------------------------
# Transactions & Interchanges
# ---------------------------
@login_required
def transaction_list(request):
    company = request.user.companyuser.company
    transactions = EDITransaction.objects.filter(company=company)
    paginator = Paginator(transactions, 20)
    page = request.GET.get("page")
    transactions_page = paginator.get_page(page)
    return render(request, "transactions/list.html", {"transactions": transactions_page})

@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(EDITransaction, id=transaction_id, company=request.user.companyuser.company)
    return render(request, "transactions/detail.html", {"transaction": transaction})

@login_required
def interchange_list(request):
    company = request.user.companyuser.company
    interchanges = Interchange.objects.filter(company=company)
    return render(request, "transactions/interchanges.html", {"interchanges": interchanges})

@login_required
def interchange_detail(request, interchange_id):
    interchange = get_object_or_404(Interchange, id=interchange_id, company=request.user.companyuser.company)
    return render(request, "transactions/interchange_detail.html", {"interchange": interchange})

@login_required
def functional_group_detail(request, group_id):
    group = get_object_or_404(FunctionalGroup, id=group_id, company=request.user.companyuser.company)
    return render(request, "transactions/group_detail.html", {"group": group})

# ---------------------------
# Analytics & Reports
# ---------------------------
@login_required
def monthly_summary_view(request):
    company = request.user.companyuser.company
    summaries = MonthlyTransactionSummary.objects.filter(company=company)
    return render(request, "analytics/monthly.html", {"summaries": summaries})

@login_required
def daily_analytics_view(request):
    company = request.user.companyuser.company
    analytics = DailyAnalytics.objects.filter(company=company)
    return render(request, "analytics/daily.html", {"analytics": analytics})

@login_required
def custom_report_view(request):
    company = request.user.companyuser.company
    reports = CustomReport.objects.filter(company=company)
    return render(request, "analytics/reports.html", {"reports": reports})

@login_required
def dashboard_api(request):
    company = request.user.companyuser.company
    total_transactions = EDITransaction.objects.filter(company=company).count()
    monthly_summary = (
        EDITransaction.objects.filter(company=company, created_at__month=timezone.now().month)
        .values("status")
        .annotate(count=Count("id"))
    )
    return JsonResponse({
        "total_transactions": total_transactions,
        "monthly_summary": list(monthly_summary),
    })

# ---------------------------
# System & Audit Logs
# ---------------------------
@login_required
def system_config_list(request):
    configs = SystemConfig.objects.all()
    return render(request, "system/configs.html", {"configs": configs})

@login_required
def api_usage_log_list(request):
    logs = APIUsageLog.objects.all().order_by("-timestamp")[:50]
    return render(request, "system/api_logs.html", {"logs": logs})

@login_required
def scbn_integration_log_list(request):
    logs = SCBNIntegrationLog.objects.all().order_by("-timestamp")[:50]
    return render(request, "system/scbn_logs.html", {"logs": logs})

@login_required
def processing_error_list(request):
    errors = ProcessingError.objects.all().order_by("-created_at")[:50]
    return render(request, "system/errors.html", {"errors": errors})

@login_required
def processing_log_list(request):
    logs = ProcessingLog.objects.all().order_by("-created_at")[:50]
    return render(request, "system/processing_logs.html", {"logs": logs})
