from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.orders.models import Order
from apps.textbooks.models import Category, Textbook


AUTO_TAG = '[AUTO_STATS]'
CATEGORY_POOL = ['计算机', '数学', '英语', '经济管理', '机械工程']


def add_months(dt: datetime, months: int) -> datetime:
    month_index = dt.month - 1 + months
    year = dt.year + month_index // 12
    month = month_index % 12 + 1
    day = min(dt.day, 28)
    return dt.replace(year=year, month=month, day=day)


def to_price(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class Command(BaseCommand):
    help = '生成统计分析演示订单数据（跨月 completed/cancelled），并确保三名学生在我的订单中可见。'

    def add_arguments(self, parser):
        parser.add_argument('--months', type=int, default=15, help='生成月份数，默认 15（建议 >= 13 以支持同比）')
        parser.add_argument('--orders-per-month', type=int, default=6, help='每月生成订单数，默认 6')
        parser.add_argument('--users', type=int, default=3, help='参与用户数，默认 3（最少 3）')
        parser.add_argument('--cancel-every', type=int, default=4, help='每 N 单生成 1 笔取消订单，默认 4')

    @transaction.atomic
    def handle(self, *args, **options):
        months = max(13, int(options['months']))
        orders_per_month = max(3, int(options['orders_per_month']))
        required_users = max(3, int(options['users']))
        cancel_every = max(2, int(options['cancel_every']))

        User = get_user_model()
        users = list(
            User.objects.filter(is_active=True, role='student').order_by('id')[:required_users]
        )
        if len(users) < 3:
            self.stdout.write(self.style.ERROR('学生用户少于 3 个，无法生成互相可见的订单数据。'))
            self.stdout.write(self.style.WARNING('请至少准备 3 个 student 角色用户后重试。'))
            return

        auto_orders = Order.objects.filter(note__startswith=AUTO_TAG)
        removed_orders = auto_orders.count()
        auto_orders.delete()

        auto_textbooks = Textbook.objects.filter(description__startswith=AUTO_TAG)
        removed_textbooks = auto_textbooks.count()
        auto_textbooks.delete()

        categories = list(Category.objects.filter(is_active=True).order_by('id')[:8])
        if not categories:
            categories = [
                Category.objects.create(name=name, level=1, sort_order=idx, is_active=True)
                for idx, name in enumerate(CATEGORY_POOL, start=1)
            ]

        base = datetime.now().replace(day=1, hour=10, minute=0, second=0, microsecond=0)
        start_month = add_months(base, -(months - 1))

        pairs = [
            (users[0], users[1]),
            (users[1], users[2]),
            (users[2], users[0]),
        ]

        transaction_types = ['sell', 'rent', 'free']
        created_orders = 0
        completed_orders = 0
        cancelled_orders = 0

        for month_idx in range(months):
            month_start = add_months(start_month, month_idx)
            for order_idx in range(orders_per_month):
                seller, buyer = pairs[(month_idx + order_idx) % len(pairs)]
                category = categories[(month_idx + order_idx) % len(categories)]
                transaction_type = transaction_types[(month_idx + order_idx) % len(transaction_types)]

                day = min(26, 2 + order_idx * 3)
                created_at = month_start.replace(day=day)
                started_at = created_at + timedelta(hours=2)
                completed_at = created_at + timedelta(days=2 + (order_idx % 5), hours=1)

                month_factor = 1 + month_idx * 0.035
                base_price = (18 + (order_idx % 5) * 7 + (month_idx % 4) * 3) * month_factor
                if transaction_type == 'free':
                    price = Decimal('0.00')
                elif transaction_type == 'rent':
                    price = to_price(base_price * 0.45)
                else:
                    price = to_price(base_price)

                textbook = Textbook.objects.create(
                    title=f'统计样例教材 {month_start.strftime("%Y%m")}-{order_idx + 1}',
                    author=f'样例作者{(order_idx % 9) + 1}',
                    isbn=f'978700{month_idx:03d}{order_idx:03d}0',
                    publisher='统计数据出版社',
                    edition=f'第{(month_idx % 4) + 1}版',
                    condition=4 if order_idx % 2 == 0 else 3,
                    description=f'{AUTO_TAG} 用于统计分析演示的自动生成教材。',
                    price=price,
                    original_price=to_price(max(float(price), 0.01) * 1.8 if price > 0 else 39.9),
                    transaction_type=transaction_type,
                    rent_duration=30 if transaction_type == 'rent' else None,
                    category=category,
                    owner=seller,
                    status='approved',
                    view_count=30 + month_idx * 6 + order_idx * 5,
                )

                is_cancelled = (created_orders + 1) % cancel_every == 0
                status = 'cancelled' if is_cancelled else 'completed'

                order = Order.objects.create(
                    textbook=textbook,
                    buyer=buyer,
                    seller=seller,
                    transaction_type=transaction_type,
                    price=price,
                    status='pending',
                    rent_start_date=created_at.date() if transaction_type == 'rent' else None,
                    rent_end_date=(created_at + timedelta(days=30)).date() if transaction_type == 'rent' else None,
                    note=f'{AUTO_TAG} 统计补数订单，seller={seller.username}, buyer={buyer.username}',
                )

                if status == 'completed':
                    Order.objects.filter(pk=order.pk).update(
                        status='completed',
                        created_at=created_at,
                        started_at=started_at,
                        completed_at=completed_at,
                        updated_at=completed_at,
                    )
                    Textbook.objects.filter(pk=textbook.pk).update(
                        created_at=created_at - timedelta(days=6),
                        updated_at=completed_at,
                        status='rented' if transaction_type == 'rent' else 'sold',
                    )
                    completed_orders += 1
                else:
                    cancelled_at = created_at + timedelta(days=1, hours=3)
                    Order.objects.filter(pk=order.pk).update(
                        status='cancelled',
                        created_at=created_at,
                        started_at=started_at,
                        completed_at=None,
                        updated_at=cancelled_at,
                    )
                    Textbook.objects.filter(pk=textbook.pk).update(
                        created_at=created_at - timedelta(days=5),
                        updated_at=cancelled_at,
                        status='approved',
                    )
                    cancelled_orders += 1

                created_orders += 1

        self.stdout.write(self.style.SUCCESS('统计订单补数完成。'))
        self.stdout.write(f'清理历史 AUTO 数据: 订单 {removed_orders} 条，教材 {removed_textbooks} 本')
        self.stdout.write(f'本次新增订单: {created_orders} 条（完成 {completed_orders}，取消 {cancelled_orders}）')
        self.stdout.write(f'参与用户: {", ".join([u.username for u in users[:3]])}')
        self.stdout.write(self.style.SUCCESS('这些用户均可在“我的订单”页看到相关记录（买/卖双方均覆盖）。'))
