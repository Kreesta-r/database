from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from .models import TradingPartner, PurchaseOrder, Invoice, Payment

def index(request):
    return JsonResponse({
        'status': 'success',
        'message': 'EDI Transactions API is running',
    })

def trading_partners(request):
    partners = TradingPartner.objects.all().values()
    return JsonResponse({
        'count': partners.count(),
        'results': list(partners)
    })

def purchase_orders(request):
    orders = PurchaseOrder.objects.all().values()
    return JsonResponse({
        'count': orders.count(),
        'results': list(orders)
    })

def invoices(request):
    invoices = Invoice.objects.all().values()
    return JsonResponse({
        'count': invoices.count(),
        'results': list(invoices)
    })

def payments(request):
    payments = Payment.objects.all().values()
    return JsonResponse({
        'count': payments.count(),
        'results': list(payments)
    })
