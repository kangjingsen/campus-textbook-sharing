import random
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from apps.statistics.models import SellerRating
from apps.orders.models import Order

User = get_user_model()


class Command(BaseCommand):
    help = '为所有有订单的卖家生成随机评分（4.0-4.8），如果已有评分则跳过'

    def add_arguments(self, parser):
        parser.add_argument(
            '--regenerate',
            action='store_true',
            help='重新生成，覆盖现有评分'
        )

    def handle(self, *args, **options):
        regenerate = options.get('regenerate', False)

        # 获取所有有完成订单的卖家
        sellers_with_orders = User.objects.filter(
            role='student',
            sell_orders__status='completed'
        ).distinct()

        self.stdout.write(f'找到 {sellers_with_orders.count()} 个有完成订单的卖家')

        created_count = 0
        skipped_count = 0
        regenerated_count = 0

        for seller in sellers_with_orders:
            # 检查是否已有评分
            existing_ratings_count = SellerRating.objects.filter(seller=seller).count()

            if existing_ratings_count > 0 and not regenerate:
                skipped_count += 1
                continue

            # 如果需要重新生成，删除旧的评分
            if regenerate and existing_ratings_count > 0:
                SellerRating.objects.filter(seller=seller).delete()
                regenerated_count += 1

            # 获取该卖家的买家（交易对方）
            buyers = User.objects.filter(
                buy_orders__seller=seller,
                buy_orders__status='completed'
            ).distinct()

            if not buyers.exists():
                self.stdout.write(self.style.WARNING(
                    f'  {seller.username} 没有找到买家'
                ))
                continue

            # 为每个买家生成一个随机评分
            for buyer in buyers:
                # 生成4.0-4.8之间的随机评分
                score_choices = [
                    Decimal('4.0'), Decimal('4.1'), Decimal('4.2'),
                    Decimal('4.3'), Decimal('4.4'), Decimal('4.5'),
                    Decimal('4.6'), Decimal('4.7'), Decimal('4.8')
                ]
                score = random.choice(score_choices)

                # 随机评价文本
                comments = [
                    '卖家很友善，交易顺利',
                    '书籍状况很好，推荐',
                    '卖家专业，值得信赖',
                    '交易快速，满意',
                    '商品质量不错，下次还来',
                    '很好的购物体验',
                    '卖家服务态度好',
                    '书籍完整，没有缺陷',
                    '卖家让我很满意',
                    '交易愉快，物超所值'
                ]
                comment = random.choice(comments)

                # 创建评分
                rating, created = SellerRating.objects.update_or_create(
                    seller=seller,
                    rater=buyer,
                    defaults={'score': score, 'comment': comment}
                )

                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f'\n生成评分完成！'))
        self.stdout.write(f'新增评分: {created_count}')
        self.stdout.write(f'已跳过（已有评分）: {skipped_count}')
        self.stdout.write(f'重新生成: {regenerated_count}')
