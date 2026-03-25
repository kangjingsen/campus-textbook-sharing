from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    textbook_title = serializers.CharField(source='textbook.title', read_only=True)
    textbook_cover = serializers.ImageField(source='textbook.cover_image', read_only=True)
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cancel_reason_display = serializers.CharField(source='get_cancel_reason_display', read_only=True)
    cancel_by_role_display = serializers.CharField(source='get_cancel_by_role_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_no', 'textbook', 'textbook_title', 'textbook_cover',
                  'buyer', 'buyer_name', 'seller', 'seller_name',
                  'transaction_type', 'price', 'status', 'status_display',
                  'rent_start_date', 'rent_end_date', 'note',
                  'cancel_reason', 'cancel_reason_display',
                  'cancel_by_role', 'cancel_by_role_display',
                  'created_at', 'updated_at', 'started_at', 'completed_at']
        read_only_fields = ['id', 'order_no', 'buyer', 'seller', 'transaction_type',
                           'price', 'created_at', 'updated_at', 'started_at', 'completed_at']


class OrderCreateSerializer(serializers.Serializer):
    textbook_id = serializers.IntegerField()
    note = serializers.CharField(required=False, default='', allow_blank=True)
    rent_start_date = serializers.DateField(required=False, allow_null=True)
    rent_end_date = serializers.DateField(required=False, allow_null=True)
