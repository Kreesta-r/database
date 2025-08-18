from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(DocumentType)
admin.site.register(TradingPartner)
admin.site.register(Interchange)
admin.site.register(FunctionalGroup)
admin.site.register(PurchaseOrder)
admin.site.register(POLineItem)
admin.site.register(Invoice)
admin.site.register(InvoiceLineItem)
admin.site.register(Payment)
admin.site.register(PaymentDetail)
admin.site.register(ProcessingError)
admin.site.register(ProcessingLog)
