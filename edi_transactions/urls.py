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
    path("partners/add/", views.partner_create, name="partner_create"),
    path("partners/<int:partner_id>/edit/", views.partner_edit, name="partner_edit"),
    path("partners/<int:partner_id>/delete/", views.partner_delete, name="partner_delete"),

    # ==============================
    # PURCHASE ORDERS
    # ==============================
    path("purchase-orders/", views.purchase_order_list, name="purchase_order_list"),
    path("purchase-orders/<int:order_id>/", views.purchase_order_detail, name="purchase_order_detail"),
    path("purchase-orders/add/", views.purchase_order_create, name="purchase_order_create"),
    path("purchase-orders/<int:order_id>/edit/", views.purchase_order_edit, name="purchase_order_edit"),
    path("purchase-orders/<int:order_id>/delete/", views.purchase_order_delete, name="purchase_order_delete"),

    # ==============================
    # INVOICES
    # ==============================
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:invoice_id>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/add/", views.invoice_create, name="invoice_create"),
    path("invoices/<int:invoice_id>/edit/", views.invoice_edit, name="invoice_edit"),
    path("invoices/<int:invoice_id>/delete/", views.invoice_delete, name="invoice_delete"),

    # ==============================
    # PAYMENTS
    # ==============================
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/<int:payment_id>/", views.payment_detail, name="payment_detail"),
    path("payments/add/", views.payment_create, name="payment_create"),
    path("payments/<int:payment_id>/edit/", views.payment_edit, name="payment_edit"),
    path("payments/<int:payment_id>/delete/", views.payment_delete, name="payment_delete"),

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
