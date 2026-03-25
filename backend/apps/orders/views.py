from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from datetime import timedelta

from apps.textbooks.models import Textbook
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer


CANCEL_REASONS = {item[0] for item in Order.CANCEL_REASON_CHOICES}


def auto_complete_expired_orders_for_user(user):
    """订单确认后 3 天自动完成（线下交易兜底）"""
    expire_at = timezone.now() - timedelta(days=3)
    expired = Order.objects.filter(
        status='confirmed',
        started_at__isnull=False,
        started_at__lte=expire_at
    ).filter(Q(buyer=user) | Q(seller=user)).select_related('textbook')

    for order in expired:
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at', 'updated_at'])

        textbook = order.textbook
        textbook.status = 'rented' if order.transaction_type == 'rent' else 'sold'
        textbook.save(update_fields=['status'])


class OrderCreateView(APIView):
    """创建订单（买方发起）"""

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        textbook_id = serializer.validated_data['textbook_id']
        with transaction.atomic():
            try:
                textbook = Textbook.objects.select_for_update().get(pk=textbook_id)
            except Textbook.DoesNotExist:
                return Response({'error': '教材不存在或已下架'}, status=status.HTTP_404_NOT_FOUND)

            if textbook.status != 'approved':
                return Response({'error': '教材不存在或已下架'}, status=status.HTTP_404_NOT_FOUND)

            if textbook.owner == request.user:
                return Response({'error': '不能购买自己的教材'}, status=status.HTTP_400_BAD_REQUEST)

            active_exists = Order.objects.filter(
                textbook=textbook,
                status__in=['pending', 'confirmed']
            ).exists()
            if active_exists:
                return Response({'error': '该教材已有进行中的订单，暂不可下单'}, status=status.HTTP_400_BAD_REQUEST)

            existing = Order.objects.filter(
                textbook=textbook, buyer=request.user,
                status__in=['pending', 'confirmed']
            ).exists()
            if existing:
                return Response({'error': '您已有该教材的未完成订单'}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(
                textbook=textbook,
                buyer=request.user,
                seller=textbook.owner,
                transaction_type=textbook.transaction_type,
                price=textbook.price,
                note=serializer.validated_data.get('note', ''),
                rent_start_date=serializer.validated_data.get('rent_start_date'),
                rent_end_date=serializer.validated_data.get('rent_end_date'),
            )

            textbook.status = 'rented' if textbook.transaction_type == 'rent' else 'sold'
            textbook.save(update_fields=['status'])

        return Response({
            'message': '订单创建成功',
            'order': OrderSerializer(order).data
        }, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    """我的订单列表"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        auto_complete_expired_orders_for_user(user)
        role = self.request.query_params.get('role', 'all')
        order_status = self.request.query_params.get('status')

        qs = Order.objects.all()
        if role == 'buyer':
            qs = qs.filter(buyer=user)
        elif role == 'seller':
            qs = qs.filter(seller=user)
        else:
            qs = qs.filter(Q(buyer=user) | Q(seller=user))

        if order_status:
            qs = qs.filter(status=order_status)
        return qs


class OrderDetailView(generics.RetrieveAPIView):
    """订单详情"""
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        auto_complete_expired_orders_for_user(user)
        return Order.objects.filter(Q(buyer=user) | Q(seller=user))


class OrderConfirmView(APIView):
    """卖方确认订单"""

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, seller=request.user, status='pending')
        except Order.DoesNotExist:
            return Response({'error': '订单不存在'}, status=status.HTTP_404_NOT_FOUND)

        order.status = 'confirmed'
        order.started_at = timezone.now()
        order.save(update_fields=['status', 'started_at', 'updated_at'])
        return Response({'message': '订单已确认'})


class OrderCompleteView(APIView):
    """完成交易"""

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, status='confirmed')
            if order.buyer != request.user and order.seller != request.user:
                raise Order.DoesNotExist
        except Order.DoesNotExist:
            return Response({'error': '订单不存在'}, status=status.HTTP_404_NOT_FOUND)

        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save(update_fields=['status', 'completed_at', 'updated_at'])

        # 更新教材状态
        textbook = order.textbook
        if order.transaction_type == 'rent':
            textbook.status = 'rented'
        else:
            textbook.status = 'sold'
        textbook.save(update_fields=['status'])

        return Response({'message': '交易已完成'})


class OrderCancelView(APIView):
    """取消订单"""

    def post(self, request, pk):
        with transaction.atomic():
            try:
                order = Order.objects.select_related('textbook').select_for_update().get(
                    pk=pk, status__in=['pending', 'confirmed']
                )
                if order.buyer != request.user and order.seller != request.user:
                    raise Order.DoesNotExist
            except Order.DoesNotExist:
                return Response({'error': '订单不存在或无法取消'}, status=status.HTTP_404_NOT_FOUND)

            reason = str(request.data.get('reason', '') or '').strip()
            if reason not in CANCEL_REASONS:
                return Response({'error': '取消原因无效，请选择预设原因'}, status=status.HTTP_400_BAD_REQUEST)

            textbook = Textbook.objects.select_for_update().get(pk=order.textbook_id)
            has_active = Order.objects.filter(
                textbook_id=textbook.id,
                status__in=['pending', 'confirmed']
            ).exclude(pk=order.pk).exists()

            cancel_by_role = 'buyer' if order.buyer_id == request.user.id else 'seller'
            order.status = 'cancelled'
            order.cancel_reason = reason
            order.cancel_by_role = cancel_by_role
            order.save(update_fields=['status', 'cancel_reason', 'cancel_by_role', 'updated_at'])

            if not has_active and textbook.status in ['sold', 'rented']:
                textbook.status = 'approved'
                textbook.save(update_fields=['status'])

        return Response({'message': '订单已取消'})


class OrderReturnView(APIView):
    """租赁归还"""

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, transaction_type='rent',
                                      status='completed', buyer=request.user)
        except Order.DoesNotExist:
            return Response({'error': '订单不存在'}, status=status.HTTP_404_NOT_FOUND)

        order.status = 'returned'
        order.save(update_fields=['status', 'updated_at'])

        # 教材重新上架
        textbook = order.textbook
        textbook.status = 'approved'
        textbook.save(update_fields=['status'])

        return Response({'message': '已归还'})
