from django.contrib import admin
from .models import User, PurchaseRequest

admin.site.register(User)
admin.site.register(PurchaseRequest)