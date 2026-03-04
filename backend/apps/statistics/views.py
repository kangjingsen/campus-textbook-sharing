from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Avg, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncDate
from django.utils import timezone
from datetime import timedelta

from apps.textbooks.models import Textbook, Category
from apps.orders.models import Order
from apps.users.models import User
from utils.permissions import IsAdmin


class DashboardOverviewView(APIView):
    """仪表盘概览数据"""
    permission_classes = [IsAdmin]

    def get(self, request):
        now = timezone.now()
        today = now.date()
        month_start = today.replace(day=1)

        data = {
            'user_count': User.objects.count(),
            'textbook_count': Textbook.objects.count(),
            'approved_textbooks': Textbook.objects.filter(status='approved').count(),
            'pending_review_count': Textbook.objects.filter(status='pending_review').count(),
            'order_count': Order.objects.count(),
            'completed_orders': Order.objects.filter(status='completed').count(),
            'today_orders': Order.objects.filter(created_at__date=today).count(),
            'month_orders': Order.objects.filter(created_at__date__gte=month_start).count(),
            'total_revenue': float(Order.objects.filter(
                status='completed'
            ).aggregate(total=Sum('price'))['total'] or 0),
        }
        return Response(data)


class CirculationRateView(APIView):
    """教材流通率 — 按月趋势"""
    permission_classes = [IsAdmin]

    def get(self, request):
        months = int(request.query_params.get('months', 12))
        start_date = timezone.now() - timedelta(days=months * 30)

        # 每月完成订单数
        monthly_orders = Order.objects.filter(
            status='completed',
            completed_at__gte=start_date
        ).annotate(
            month=TruncMonth('completed_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        # 每月教材发布数
        monthly_textbooks = Textbook.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        textbook_map = {
            item['month'].strftime('%Y-%m'): item['count']
            for item in monthly_textbooks
        }

        result = []
        for item in monthly_orders:
            month_str = item['month'].strftime('%Y-%m')
            total_textbooks = textbook_map.get(month_str, 0)
            rate = (item['count'] / total_textbooks * 100) if total_textbooks > 0 else 0
            result.append({
                'month': month_str,
                'count': item['count'],
                'completed_orders': item['count'],
                'published_textbooks': total_textbooks,
                'circulation_rate': round(rate, 2)
            })

        return Response(result)


class PopularTextbookRankView(APIView):
    """热门教材排行"""
    permission_classes = [IsAdmin]

    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        rank_by = request.query_params.get('rank_by') or request.query_params.get('type', 'comprehensive')

        textbooks = Textbook.objects.filter(
            status__in=['approved', 'sold', 'rented', 'completed']
        ).annotate(
            order_count=Count('orders', filter=Q(orders__status='completed'))
        )

        if rank_by == 'views':
            textbooks = textbooks.order_by('-view_count')
        elif rank_by == 'orders':
            textbooks = textbooks.order_by('-order_count')
        else:
            # 综合得分 = view_count * 0.3 + order_count * 0.7 * 100
            textbooks = textbooks.order_by('-order_count', '-view_count')

        result = []
        for tb in textbooks[:limit]:
            result.append({
                'id': tb.id,
                'title': tb.title,
                'author': tb.author,
                'category': tb.category.name if tb.category else '',
                'view_count': tb.view_count,
                'order_count': tb.order_count,
                'price': float(tb.price),
            })

        return Response(result)


class PriceTrendView(APIView):
    """价格走势 — 按分类维度"""
    permission_classes = [IsAdmin]

    def get(self, request):
        months = int(request.query_params.get('months', 12))
        category_id = request.query_params.get('category_id')
        start_date = timezone.now() - timedelta(days=months * 30)

        qs = Order.objects.filter(
            status='completed',
            completed_at__gte=start_date,
            price__gt=0
        )

        if category_id:
            qs = qs.filter(textbook__category_id=category_id)

        # 按分类和月份分组，前端需要 category 字段来画多条折线
        monthly_prices = qs.annotate(
            month=TruncMonth('completed_at')
        ).values('month', 'textbook__category__name').annotate(
            avg_price=Avg('price'),
            total_orders=Count('id'),
            total_revenue=Sum('price')
        ).order_by('month')

        result = [{
            'month': item['month'].strftime('%Y-%m'),
            'category': item['textbook__category__name'] or '未分类',
            'avg_price': round(float(item['avg_price']), 2),
            'total_orders': item['total_orders'],
            'total_revenue': float(item['total_revenue'])
        } for item in monthly_prices]

        return Response(result)


class CollegeDemandView(APIView):
    """学院需求分布"""
    permission_classes = [IsAdmin]

    def get(self, request):
        college_demand = Order.objects.filter(
            status='completed'
        ).values(
            college=F('buyer__college')
        ).annotate(
            order_count=Count('id'),
            total_amount=Sum('price')
        ).order_by('-order_count')

        result = [{
            'college': item['college'] or '未知',
            'count': item['order_count'],
            'order_count': item['order_count'],
            'total_amount': float(item['total_amount'] or 0)
        } for item in college_demand]

        return Response(result)


class TransactionTypeDistView(APIView):
    """交易类型分布"""
    permission_classes = [IsAdmin]

    def get(self, request):
        type_dist = Order.objects.filter(
            status='completed'
        ).values('transaction_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # 前端期望 {sell: N, rent: N, free: N} 格式的对象
        result = {item['transaction_type']: item['count'] for item in type_dist}
        # 确保三种类型都有值
        for t in ('sell', 'rent', 'free'):
            result.setdefault(t, 0)

        return Response(result)


class UserActivityView(APIView):
    """用户活跃度趋势"""
    permission_classes = [IsAdmin]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)

        # 按天统计下单的不同用户数
        daily_active = Order.objects.filter(
            created_at__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            active_buyers=Count('buyer', distinct=True),
            active_sellers=Count('seller', distinct=True),
            total_orders=Count('id')
        ).order_by('date')

        result = [{
            'date': item['date'].strftime('%Y-%m-%d'),
            'count': item['active_buyers'] + item['active_sellers'],
            'active_buyers': item['active_buyers'],
            'active_sellers': item['active_sellers'],
            'total_orders': item['total_orders']
        } for item in daily_active]

        return Response(result)


class CategoryDistributionView(APIView):
    """分类教材分布"""
    permission_classes = [IsAdmin]

    def get(self, request):
        categories = Category.objects.filter(
            is_active=True
        ).annotate(
            textbook_count=Count('textbooks'),
            order_count=Count('textbooks__orders', filter=Q(textbooks__orders__status='completed'))
        ).values(
            'id', 'name', 'level', 'textbook_count', 'order_count'
        ).order_by('-textbook_count')

        # 前端期望 count 和 category 字段名
        result = [{
            'category': item['name'],
            'count': item['textbook_count'],
            'id': item['id'],
            'level': item['level'],
            'order_count': item['order_count'],
        } for item in categories]

        return Response(result)
