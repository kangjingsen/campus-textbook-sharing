from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from apps.textbooks.models import Textbook
from .models import Order
from .serializers import OrderSerializer, OrderCreateSerializer


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
        try:
            textbook = Textbook.objects.get(pk=textbook_id, status='approved')
        except Textbook.DoesNotExist:
            return Response({'error': '教材不存在或已下架'}, status=status.HTTP_404_NOT_FOUND)

        if textbook.owner == request.user:
            return Response({'error': '不能购买自己的教材'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查是否已有未完成的订单
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
        try:
            order = Order.objects.get(pk=pk, status__in=['pending', 'confirmed'])
            if order.buyer != request.user and order.seller != request.user:
                raise Order.DoesNotExist
        except Order.DoesNotExist:
            return Response({'error': '订单不存在或无法取消'}, status=status.HTTP_404_NOT_FOUND)

        order.status = 'cancelled'
        order.save(update_fields=['status', 'updated_at'])
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
