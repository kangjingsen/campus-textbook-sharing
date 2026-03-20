from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum, Q, F
from django.db.models.functions import TruncMonth, TruncWeek, TruncDate
from django.utils import timezone
from datetime import timedelta
from statistics import median

from apps.textbooks.models import Textbook, Category
from apps.textbooks.models import ResourceOrder
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

        textbook_order_count = Order.objects.count()
        textbook_completed_orders = Order.objects.filter(status='completed').count()
        textbook_cancelled_orders = Order.objects.filter(status='cancelled').count()
        textbook_today_orders = Order.objects.filter(created_at__date=today).count()
        textbook_month_orders = Order.objects.filter(created_at__date__gte=month_start).count()
        textbook_revenue = float(Order.objects.filter(
            status='completed'
        ).aggregate(total=Sum('price'))['total'] or 0)

        resource_order_count = ResourceOrder.objects.count()
        resource_completed_orders = ResourceOrder.objects.filter(status='completed').count()
        resource_cancelled_orders = ResourceOrder.objects.filter(status='cancelled').count()
        resource_today_orders = ResourceOrder.objects.filter(created_at__date=today).count()
        resource_month_orders = ResourceOrder.objects.filter(created_at__date__gte=month_start).count()
        resource_revenue = float(ResourceOrder.objects.filter(
            status='completed'
        ).aggregate(total=Sum('price'))['total'] or 0)

        total_order_count = textbook_order_count + resource_order_count
        total_completed_orders = textbook_completed_orders + resource_completed_orders
        total_cancelled_orders = textbook_cancelled_orders + resource_cancelled_orders
        total_today_orders = textbook_today_orders + resource_today_orders
        total_month_orders = textbook_month_orders + resource_month_orders
        total_revenue = textbook_revenue + resource_revenue

        data = {
            'user_count': User.objects.count(),
            'textbook_count': Textbook.objects.count(),
            'approved_textbooks': Textbook.objects.filter(status='approved').count(),
            'pending_review_count': Textbook.objects.filter(status='pending_review').count(),
            'order_count': total_order_count,
            'completed_orders': total_completed_orders,
            'cancelled_orders': total_cancelled_orders,
            'today_orders': total_today_orders,
            'month_orders': total_month_orders,
            'total_revenue': total_revenue,
            'textbook_order_count': textbook_order_count,
            'textbook_completed_orders': textbook_completed_orders,
            'textbook_cancelled_orders': textbook_cancelled_orders,
            'resource_order_count': resource_order_count,
            'resource_completed_orders': resource_completed_orders,
            'resource_cancelled_orders': resource_cancelled_orders,
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
            total_order_count=Count('orders', filter=Q(orders__status__in=['pending', 'confirmed', 'completed', 'cancelled'])),
            completed_order_count=Count('orders', filter=Q(orders__status='completed')),
            cancelled_order_count=Count('orders', filter=Q(orders__status='cancelled'))
        )

        if rank_by == 'views':
            textbooks = textbooks.order_by('-view_count')
        elif rank_by == 'orders':
            # 按订单数口径：包含取消订单，反映真实需求热度
            textbooks = textbooks.order_by('-total_order_count', '-completed_order_count', '-view_count')
        else:
            # 综合得分 = view_count * 0.3 + order_count * 0.7 * 100
            textbooks = textbooks.order_by('-total_order_count', '-view_count')

        result = []
        for tb in textbooks[:limit]:
            result.append({
                'id': tb.id,
                'title': tb.title,
                'author': tb.author,
                'category': tb.category.name if tb.category else '',
                'view_count': tb.view_count,
                'order_count': tb.total_order_count,
                'completed_order_count': tb.completed_order_count,
                'cancelled_order_count': tb.cancelled_order_count,
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
        textbook_college_demand = Order.objects.values(
            college=F('buyer__college')
        ).annotate(
            order_count=Count('id'),
            completed_count=Count('id', filter=Q(status='completed')),
            cancelled_count=Count('id', filter=Q(status='cancelled')),
            total_amount=Sum('price', filter=Q(status='completed'))
        )

        resource_college_demand = ResourceOrder.objects.values(
            college=F('buyer__college')
        ).annotate(
            order_count=Count('id'),
            completed_count=Count('id', filter=Q(status='completed')),
            cancelled_count=Count('id', filter=Q(status='cancelled')),
            total_amount=Sum('price', filter=Q(status='completed'))
        )

        college_map = {}
        for item in textbook_college_demand:
            key = item['college'] or '未知'
            college_map[key] = {
                'college': key,
                'order_count': item['order_count'],
                'completed_count': item['completed_count'],
                'cancelled_count': item['cancelled_count'],
                'total_amount': float(item['total_amount'] or 0),
                'textbook_order_count': item['order_count'],
                'resource_order_count': 0,
            }

        for item in resource_college_demand:
            key = item['college'] or '未知'
            if key not in college_map:
                college_map[key] = {
                    'college': key,
                    'order_count': 0,
                    'completed_count': 0,
                    'cancelled_count': 0,
                    'total_amount': 0.0,
                    'textbook_order_count': 0,
                    'resource_order_count': 0,
                }

            college_map[key]['order_count'] += item['order_count']
            college_map[key]['completed_count'] += item['completed_count']
            college_map[key]['cancelled_count'] += item['cancelled_count']
            college_map[key]['total_amount'] += float(item['total_amount'] or 0)
            college_map[key]['resource_order_count'] += item['order_count']

        college_demand = sorted(college_map.values(), key=lambda x: x['order_count'], reverse=True)

        result = []
        for item in college_demand:
            result.append({
                'college': item['college'],
                'count': item['order_count'],
                'order_count': item['order_count'],
                'completed_count': item['completed_count'],
                'cancelled_count': item['cancelled_count'],
                'total_amount': item['total_amount'],
                'textbook_order_count': item['textbook_order_count'],
                'resource_order_count': item['resource_order_count'],
            })

        return Response(result)


class TransactionTypeDistView(APIView):
    """交易类型分布"""
    permission_classes = [IsAdmin]

    def get(self, request):
        type_dist = Order.objects.values('transaction_type').annotate(
            count=Count('id')
        ).order_by('-count')

        textbook_cancelled_count = Order.objects.filter(status='cancelled').count()
        resource_cancelled_count = ResourceOrder.objects.filter(status='cancelled').count()

        # 前端期望 {sell: N, rent: N, free: N} 格式的对象
        result = {item['transaction_type']: item['count'] for item in type_dist}
        # 确保三种类型都有值
        for t in ('sell', 'rent', 'free'):
            result.setdefault(t, 0)
        result['cancelled_count'] = textbook_cancelled_count + resource_cancelled_count
        result['textbook_cancelled_count'] = textbook_cancelled_count
        result['resource_cancelled_count'] = resource_cancelled_count

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

        textbook_monthly_total = Order.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        textbook_monthly_cancelled = Order.objects.filter(
            status='cancelled',
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        resource_monthly_total = ResourceOrder.objects.filter(
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        resource_monthly_cancelled = ResourceOrder.objects.filter(
            status='cancelled',
            created_at__gte=start_date
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(count=Count('id')).order_by('month')

        textbook_total_map = {item['month'].strftime('%Y-%m'): item['count'] for item in textbook_monthly_total}
        textbook_cancelled_map = {item['month'].strftime('%Y-%m'): item['count'] for item in textbook_monthly_cancelled}
        resource_total_map = {item['month'].strftime('%Y-%m'): item['count'] for item in resource_monthly_total}
        resource_cancelled_map = {item['month'].strftime('%Y-%m'): item['count'] for item in resource_monthly_cancelled}

        total_map = {}
        cancelled_map = {}
        for month_key in set(textbook_total_map.keys()) | set(resource_total_map.keys()):
            total_map[month_key] = textbook_total_map.get(month_key, 0) + resource_total_map.get(month_key, 0)
        for month_key in set(textbook_cancelled_map.keys()) | set(resource_cancelled_map.keys()):
            cancelled_map[month_key] = textbook_cancelled_map.get(month_key, 0) + resource_cancelled_map.get(month_key, 0)

        month_keys = sorted(set(total_map.keys()) | set(cancelled_map.keys()))

        trend = []
        for month_key in month_keys:
            total_count = total_map.get(month_key, 0)
            cancelled_count = cancelled_map.get(month_key, 0)
            trend.append({
                'month': month_key,
                'total_orders': total_count,
                'cancelled_orders': cancelled_count,
                'textbook_total_orders': textbook_total_map.get(month_key, 0),
                'textbook_cancelled_orders': textbook_cancelled_map.get(month_key, 0),
                'resource_total_orders': resource_total_map.get(month_key, 0),
                'resource_cancelled_orders': resource_cancelled_map.get(month_key, 0),
                'cancel_rate': round(cancelled_count / total_count * 100, 2) if total_count else 0
            })

        textbook_by_category = Order.objects.filter(
            status='cancelled', created_at__gte=start_date
        ).values(
            category=F('textbook__category__name')
        ).annotate(
            count=Count('id')
        )

        resource_by_category = ResourceOrder.objects.filter(
            status='cancelled', created_at__gte=start_date
        ).values(
            category=F('resource__category__name')
        ).annotate(
            count=Count('id')
        )

        category_map = {}
        for item in textbook_by_category:
            key = item['category'] or '未分类'
            category_map[key] = category_map.get(key, 0) + item['count']
        for item in resource_by_category:
            key = item['category'] or '未分类'
            category_map[key] = category_map.get(key, 0) + item['count']

        by_category = sorted(
            [{'category': key, 'count': value} for key, value in category_map.items()],
            key=lambda x: x['count'],
            reverse=True
        )[:limit]

        textbook_by_seller = Order.objects.filter(
            status='cancelled', created_at__gte=start_date
        ).values(
            seller_user_id=F('seller__id'),
            seller_name=F('seller__username')
        ).annotate(
            count=Count('id'),
            amount=Sum('price')
        )

        resource_by_seller = ResourceOrder.objects.filter(
            status='cancelled', created_at__gte=start_date
        ).values(
            seller_user_id=F('seller__id'),
            seller_name=F('seller__username')
        ).annotate(
            count=Count('id'),
            amount=Sum('price')
        )

        seller_map = {}
        for item in textbook_by_seller:
            sid = item['seller_user_id']
            seller_map[sid] = {
                'seller_id': sid,
                'seller_name': item['seller_name'],
                'count': item['count'],
                'amount': float(item['amount'] or 0)
            }
        for item in resource_by_seller:
            sid = item['seller_user_id']
            if sid not in seller_map:
                seller_map[sid] = {
                    'seller_id': sid,
                    'seller_name': item['seller_name'],
                    'count': 0,
                    'amount': 0.0
                }
            seller_map[sid]['count'] += item['count']
            seller_map[sid]['amount'] += float(item['amount'] or 0)

        by_seller = sorted(seller_map.values(), key=lambda x: x['count'], reverse=True)[:limit]

        textbook_cancel_total = Order.objects.filter(
            status='cancelled', created_at__gte=start_date
        ).count()
        resource_cancel_total = ResourceOrder.objects.filter(
            status='cancelled', created_at__gte=start_date
        ).count()

        return Response({
            'trend': trend,
            'by_category': by_category,
            'by_seller': by_seller,
            'summary': {
                'textbook_cancelled_orders': textbook_cancel_total,
                'resource_cancelled_orders': resource_cancel_total,
                'total_cancelled_orders': textbook_cancel_total + resource_cancel_total
            }
        })


class UserInsightsView(APIView):
    """用户可见统计：我的概览、积压排行、需求排行快照"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        limit = int(request.query_params.get('limit', 10))

        my_textbooks_qs = Textbook.objects.filter(owner=user)
        my_active_qs = my_textbooks_qs.filter(status='approved')
        my_completed_orders = Order.objects.filter(seller=user, status='completed')

        # 积压定义：在架且未完成交易，按在架天数和低浏览优先排序
        backlog_candidates = my_active_qs.annotate(
            completed_order_count=Count('orders', filter=Q(orders__status='completed')),
            pending_order_count=Count('orders', filter=Q(orders__status__in=['pending', 'confirmed']))
        ).filter(completed_order_count=0)

        backlog_items = []
        now = timezone.now()
        for tb in backlog_candidates:
            days_on_shelf = (now.date() - tb.created_at.date()).days
            backlog_score = days_on_shelf * 2 + max(0, 30 - int(tb.view_count or 0))
            backlog_items.append({
                'textbook_id': tb.id,
                'title': tb.title,
                'category': tb.category.name if tb.category else '未分类',
                'price': float(tb.price or 0),
                'view_count': int(tb.view_count or 0),
                'pending_order_count': int(tb.pending_order_count or 0),
                'days_on_shelf': days_on_shelf,
                'backlog_score': backlog_score,
                'suggestion': '建议降价或下架' if days_on_shelf >= 30 else '建议优化标题和描述'
            })

        backlog_items.sort(key=lambda x: (x['backlog_score'], x['days_on_shelf']), reverse=True)

        # 全站需求榜（用户可见精简版）
        wish_data = WishlistItem.objects.filter(status='open').values('title').annotate(
            wishlist_count=Count('id')
        )
        wish_map = {i['title']: i['wishlist_count'] for i in wish_data if i['title']}

        order_data = Order.objects.filter(
            status__in=['pending', 'confirmed', 'completed', 'cancelled']
        ).values('textbook__title').annotate(order_count=Count('id'))
        order_map = {i['textbook__title']: i['order_count'] for i in order_data if i['textbook__title']}

        demand_rows = []
        for title in (set(wish_map.keys()) | set(order_map.keys())):
            wishlist_count = int(wish_map.get(title, 0))
            order_count = int(order_map.get(title, 0))
            demand_rows.append({
                'title': title,
                'wishlist_count': wishlist_count,
                'order_count': order_count,
                'demand_score': wishlist_count * 2 + order_count
            })
        demand_rows.sort(key=lambda x: x['demand_score'], reverse=True)

        return Response({
            'overview': {
                'my_total_textbooks': my_textbooks_qs.count(),
                'my_active_textbooks': my_active_qs.count(),
                'my_backlog_count': len(backlog_items),
                'my_completed_orders': my_completed_orders.count(),
                'my_sales_amount': float(my_completed_orders.aggregate(total=Sum('price'))['total'] or 0),
            },
            'backlog_ranking': backlog_items[:limit],
            'demand_ranking': demand_rows[:limit]
        })
