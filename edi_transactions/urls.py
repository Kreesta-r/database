from django.urls import path
from . import views

app_name = "edi_transactions"

urlpatterns = [
    # ==============================
    # AUTHENTICATION
    # ==============================
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ==============================
    # DASHBOARD
    # ==============================
    path("dashboard/", views.dashboard, name="dashboard"),

    # ==============================
    # TRANSACTIONS
    # ==============================
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/<int:transaction_id>/", views.transaction_detail, name="transaction_detail"),

    # ==============================
    # TRADING PARTNERS
    # ==============================
    path("partners/", views.partner_list, name="partner_list"),
    path("partners/<int:partner_id>/", views.partner_detail, name="partner_detail"),

    # ==============================
    # PURCHASE ORDERS
    # ==============================
    path("purchase-orders/", views.purchase_order_list, name="purchase_order_list"),
    path("purchase-orders/<int:order_id>/", views.purchase_order_detail, name="purchase_order_detail"),

    # ==============================
    # INVOICES
    # ==============================
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:invoice_id>/", views.invoice_detail, name="invoice_detail"),

    # ==============================
    # PAYMENTS
    # ==============================
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/<int:payment_id>/", views.payment_detail, name="payment_detail"),

    # ==============================
    # REPORTS (HTML only)
    # ==============================
    path("reports/", views.report_list, name="report_list"),
    path("reports/<int:report_id>/", views.report_detail, name="report_detail"),

    # ==============================
    # SYSTEM LOGS
    # ==============================
    path("logs/scbn/", views.scbn_log_list, name="scbn_log_list"),
    path("logs/workflow/", views.workflow_list, name="workflow_list"),
]
