from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Avg, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncDate
from django.utils import timezone
from datetime import timedelta
from statistics import median

from apps.textbooks.models import Textbook, Category
from apps.orders.models import Order
from apps.users.models import User
from apps.recommendations.models import WishlistItem
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
            'cancelled_orders': Order.objects.filter(status='cancelled').count(),
            'today_orders': Order.objects.filter(created_at__date=today).count(),
            'month_orders': Order.objects.filter(created_at__date__gte=month_start).count(),
            'total_revenue': float(Order.objects.filter(
                status='completed'
            ).aggregate(total=Sum('price'))['total'] or 0),
        }
        data['cancellation_rate'] = round(
            data['cancelled_orders'] / data['order_count'] * 100, 2
        ) if data['order_count'] else 0
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

        monthly_cancelled = Order.objects.filter(
            status='cancelled',
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
        cancelled_map = {
            item['month'].strftime('%Y-%m'): item['count']
            for item in monthly_cancelled
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
                'cancelled_orders': cancelled_map.get(month_str, 0),
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
        college_demand = Order.objects.values(
            college=F('buyer__college')
        ).annotate(
            order_count=Count('id'),
            completed_count=Count('id', filter=Q(status='completed')),
            cancelled_count=Count('id', filter=Q(status='cancelled')),
            total_amount=Sum('price', filter=Q(status='completed'))
        ).order_by('-order_count')

        result = [{
            'college': item['college'] or '未知',
            'count': item['order_count'],
            'order_count': item['order_count'],
            'completed_count': item['completed_count'],
            'cancelled_count': item['cancelled_count'],
            'total_amount': float(item['total_amount'] or 0)
        } for item in college_demand]

        return Response(result)


class TransactionTypeDistView(APIView):
    """交易类型分布"""
    permission_classes = [IsAdmin]

    def get(self, request):
        type_dist = Order.objects.values('transaction_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # 前端期望 {sell: N, rent: N, free: N} 格式的对象
        result = {item['transaction_type']: item['count'] for item in type_dist}
        # 确保三种类型都有值
        for t in ('sell', 'rent', 'free'):
            result.setdefault(t, 0)
        result['cancelled_count'] = Order.objects.filter(status='cancelled').count()

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
            order_count=Count('textbooks__orders', filter=Q(textbooks__orders__status='completed')),
            cancelled_order_count=Count('textbooks__orders', filter=Q(textbooks__orders__status='cancelled'))
        ).values(
            'id', 'name', 'level', 'textbook_count', 'order_count', 'cancelled_order_count'
        ).order_by('-textbook_count')

        # 前端期望 count 和 category 字段名
        result = [{
            'category': item['name'],
            'count': item['textbook_count'],
            'id': item['id'],
            'level': item['level'],
            'order_count': item['order_count'],
            'cancelled_order_count': item['cancelled_order_count'],
        } for item in categories]

        return Response(result)


class SalesRankingView(APIView):
    """售卖排行榜（卖家维度）"""
    permission_classes = [IsAdmin]

    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        data = User.objects.filter(role='student').annotate(
            completed_orders=Count('sell_orders', filter=Q(sell_orders__status='completed')),
            cancelled_orders=Count('sell_orders', filter=Q(sell_orders__status='cancelled')),
            sales_amount=Sum('sell_orders__price', filter=Q(sell_orders__status='completed'))
        ).order_by('-sales_amount', '-completed_orders')[:limit]

        return Response([
            {
                'seller_id': u.id,
                'seller_name': u.username,
                'college': u.college,
                'completed_orders': u.completed_orders,
                'cancelled_orders': u.cancelled_orders,
                'sales_amount': float(u.sales_amount or 0),
            } for u in data
        ])


class DemandRankingView(APIView):
    """需求排行榜（结合心愿单+订单）"""
    permission_classes = [IsAdmin]

    def get(self, request):
        limit = int(request.query_params.get('limit', 20))

        wish_data = WishlistItem.objects.filter(status='open').values('title').annotate(
            wishlist_count=Count('id')
        )
        wish_map = {i['title']: i['wishlist_count'] for i in wish_data if i['title']}

        order_data = Order.objects.filter(status__in=['pending', 'confirmed', 'completed', 'cancelled']).values(
            'textbook__title'
        ).annotate(order_count=Count('id'))
        order_map = {i['textbook__title']: i['order_count'] for i in order_data if i['textbook__title']}

        titles = set(wish_map.keys()) | set(order_map.keys())
        merged = []
        for title in titles:
            w = wish_map.get(title, 0)
            o = order_map.get(title, 0)
            merged.append({
                'title': title,
                'wishlist_count': w,
                'order_count': o,
                'demand_score': w * 2 + o
            })

        merged.sort(key=lambda x: x['demand_score'], reverse=True)
        return Response(merged[:limit])


class TopSellersView(APIView):
    """优秀商家（成交额+完成率）"""
    permission_classes = [IsAdmin]

    def get(self, request):
        limit = int(request.query_params.get('limit', 20))
        sellers = User.objects.filter(role='student').annotate(
            total_orders=Count('sell_orders'),
            completed_orders=Count('sell_orders', filter=Q(sell_orders__status='completed')),
            cancelled_orders=Count('sell_orders', filter=Q(sell_orders__status='cancelled')),
            sales_amount=Sum('sell_orders__price', filter=Q(sell_orders__status='completed'))
        )

        result = []
        for s in sellers:
            completion_rate = (s.completed_orders / s.total_orders * 100) if s.total_orders else 0
            score = float(s.sales_amount or 0) * 0.6 + completion_rate * 0.4
            result.append({
                'seller_id': s.id,
                'seller_name': s.username,
                'college': s.college,
                'total_orders': s.total_orders,
                'completed_orders': s.completed_orders,
                'cancelled_orders': s.cancelled_orders,
                'completion_rate': round(completion_rate, 2),
                'sales_amount': float(s.sales_amount or 0),
                'score': round(score, 2)
            })

        result.sort(key=lambda x: x['score'], reverse=True)
        return Response(result[:limit])


class PriceMetricsView(APIView):
    """价格指数与统计指标（月度：均值/中位数/最大最小/环比/同比）"""
    permission_classes = [IsAdmin]

    def get(self, request):
        months = int(request.query_params.get('months', 12))
        start_date = timezone.now() - timedelta(days=months * 30)

        monthly_orders = Order.objects.filter(
            status='completed',
            completed_at__gte=start_date,
            price__gt=0
        ).annotate(month=TruncMonth('completed_at')).values('month', 'price').order_by('month')

        bucket = {}
        for row in monthly_orders:
            key = row['month'].strftime('%Y-%m')
            bucket.setdefault(key, []).append(float(row['price']))

        months_sorted = sorted(bucket.keys())
        metrics = []
        base_avg = None
        for idx, month_key in enumerate(months_sorted):
            values = bucket[month_key]
            avg_price = sum(values) / len(values)
            med = median(values)
            min_price = min(values)
            max_price = max(values)

            if base_avg is None:
                base_avg = avg_price
            price_index = (avg_price / base_avg * 100) if base_avg else 100

            prev_avg = None
            if idx > 0:
                prev_vals = bucket[months_sorted[idx - 1]]
                prev_avg = sum(prev_vals) / len(prev_vals)
            mom = ((avg_price - prev_avg) / prev_avg * 100) if prev_avg else None

            yoy = None
            if idx >= 12:
                yoy_vals = bucket[months_sorted[idx - 12]]
                yoy_avg = sum(yoy_vals) / len(yoy_vals)
                yoy = ((avg_price - yoy_avg) / yoy_avg * 100) if yoy_avg else None

            metrics.append({
                'month': month_key,
                'count': len(values),
                'avg_price': round(avg_price, 2),
                'median_price': round(med, 2),
                'min_price': round(min_price, 2),
                'max_price': round(max_price, 2),
                'price_index': round(price_index, 2),
                'mom': round(mom, 2) if mom is not None else None,
                'yoy': round(yoy, 2) if yoy is not None else None,
            })

        return Response({'metrics': metrics})


class WishlistDemandView(APIView):
    """心愿单需求统计"""
    permission_classes = [IsAdmin]

    def get(self, request):
        by_category = WishlistItem.objects.filter(status='open').values(
            category_name=F('category__name')
        ).annotate(count=Count('id')).order_by('-count')

        top_titles = WishlistItem.objects.filter(status='open').values('title').annotate(
            count=Count('id')
        ).order_by('-count')[:20]

        return Response({
            'total_open_wishes': WishlistItem.objects.filter(status='open').count(),
            'by_category': [{'category': i['category_name'] or '未分类', 'count': i['count']} for i in by_category],
            'top_titles': list(top_titles)
        })


class CancellationInsightsView(APIView):
    """取消订单专题分析"""
    permission_classes = [IsAdmin]

    def get(self, request):
        months = int(request.query_params.get('months', 12))
        limit = int(request.query_params.get('limit', 10))
        start_date = timezone.now() - timedelta(days=months * 30)

        monthly_total = Order.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        monthly_cancelled = Order.objects.filter(
            status='cancelled',
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        total_map = {item['month'].strftime('%Y-%m'): item['count'] for item in monthly_total}
        cancelled_map = {item['month'].strftime('%Y-%m'): item['count'] for item in monthly_cancelled}
        month_keys = sorted(set(total_map.keys()) | set(cancelled_map.keys()))

        trend = []
        for month_key in month_keys:
            total_count = total_map.get(month_key, 0)
            cancelled_count = cancelled_map.get(month_key, 0)
            trend.append({
                'month': month_key,
                'total_orders': total_count,
                'cancelled_orders': cancelled_count,
                'cancel_rate': round(cancelled_count / total_count * 100, 2) if total_count else 0
            })

        by_category = Order.objects.filter(status='cancelled').values(
            category=F('textbook__category__name')
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:limit]

        by_seller = Order.objects.filter(status='cancelled').values(
            seller_user_id=F('seller__id'),
            seller_name=F('seller__username')
        ).annotate(
            count=Count('id'),
            amount=Sum('price')
        ).order_by('-count')[:limit]

        return Response({
            'trend': trend,
            'by_category': [
                {'category': item['category'] or '未分类', 'count': item['count']}
                for item in by_category
            ],
            'by_seller': [
                {
                    'seller_id': item['seller_user_id'],
                    'seller_name': item['seller_name'],
                    'count': item['count'],
                    'amount': float(item['amount'] or 0)
                }
                for item in by_seller
            ]
        })
