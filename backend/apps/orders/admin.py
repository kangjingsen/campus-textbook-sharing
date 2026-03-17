from django.contrib import admin
from .models import Order

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_no', 'textbook', 'buyer', 'seller', 'transaction_type', 'price', 'status', 'created_at', 'started_at', 'completed_at']
    list_filter = ['status', 'transaction_type']
    search_fields = ['order_no', 'textbook__title']
