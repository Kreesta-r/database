from django.urls import path
from . import views

app_name = 'edi_transactions'

urlpatterns = [
    path('', views.index, name='index'),
    path('trading-partners/', views.trading_partners, name='trading_partners'),
    path('purchase-orders/', views.purchase_orders, name='purchase_orders'),
    path('invoices/', views.invoices, name='invoices'),
    path('payments/', views.payments, name='payments'),
]
