from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.orders.models import Order
from apps.textbooks.models import Textbook, SharedResource, ResourceOrder


PUBLISHED_STATUSES = {'approved', 'sold', 'rented', 'completed', 'offline'}


class Command(BaseCommand):
    help = '将教材、教材订单、资料订单均匀重分配到前 N 个活跃用户，并同步教材状态。'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=24, help='参与重分配的用户数，默认 24')
        parser.add_argument('--dry-run', action='store_true', help='仅预览，不落库')

    @transaction.atomic
    def handle(self, *args, **options):
        user_count = max(1, int(options['users']))
        dry_run = bool(options['dry_run'])

        User = get_user_model()
        users = list(User.objects.filter(is_active=True).order_by('id')[:user_count])
        if len(users) < user_count:
            self.stdout.write(self.style.ERROR(f'活跃用户不足 {user_count} 人，当前仅 {len(users)} 人。'))
            return

        textbooks = list(Textbook.objects.all().order_by('id'))
        textbooks_by_id = {tb.id: tb for tb in textbooks}
        orders = list(Order.objects.select_related('textbook').all().order_by('id'))
        resources = list(SharedResource.objects.all().order_by('id'))
        resource_orders = list(ResourceOrder.objects.select_related('resource').all().order_by('id'))

        self.stdout.write(
            f'准备重分配: 用户 {len(users)} 人, 教材 {len(textbooks)} 本, '
            f'教材订单 {len(orders)} 条, 资料 {len(resources)} 个, 资料订单 {len(resource_orders)} 条'
        )

        owner_map = {}
        for idx, textbook in enumerate(textbooks):
            owner = users[idx % len(users)]
            owner_map[textbook.id] = owner
            textbook.owner = owner
            if textbook.status not in PUBLISHED_STATUSES:
                textbook.status = 'approved'

        uploader_map = {}
        for idx, resource in enumerate(resources):
            uploader = users[idx % len(users)]
            uploader_map[resource.id] = uploader
            resource.uploader = uploader

        order_buyer_assignments = 0
        for idx, order in enumerate(orders):
            seller = owner_map.get(order.textbook_id) or users[idx % len(users)]
            buyer = users[(idx + 1) % len(users)]
            if buyer.id == seller.id:
                buyer = users[(idx + 2) % len(users)]

            order.seller = seller
            order.buyer = buyer
            order_buyer_assignments += 1

            # 同步教材状态，确保统计分析读取一致
            textbook = textbooks_by_id.get(order.textbook_id)
            if not textbook:
                continue
            if order.status == 'completed':
                textbook.status = 'rented' if order.transaction_type == 'rent' else 'sold'
            elif order.status in ('returned', 'cancelled', 'pending', 'confirmed'):
                textbook.status = 'approved'

        resource_order_buyer_assignments = 0
        for idx, order in enumerate(resource_orders):
            seller = uploader_map.get(order.resource_id) or users[idx % len(users)]
            buyer = users[(idx + 1) % len(users)]
            if buyer.id == seller.id:
                buyer = users[(idx + 2) % len(users)]

            order.seller = seller
            order.buyer = buyer
            resource_order_buyer_assignments += 1

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run 模式：已计算但未写入数据库。'))
            transaction.set_rollback(True)
            return

        if textbooks:
            Textbook.objects.bulk_update(textbooks, ['owner', 'status'])
        if resources:
            SharedResource.objects.bulk_update(resources, ['uploader'])
        if orders:
            Order.objects.bulk_update(orders, ['seller', 'buyer'])
        if resource_orders:
            ResourceOrder.objects.bulk_update(resource_orders, ['seller', 'buyer'])

        self.stdout.write(self.style.SUCCESS('数据重分配完成。'))
        self.stdout.write(f'教材 owner 重分配: {len(textbooks)}')
        self.stdout.write(f'教材订单 buyer/seller 重分配: {order_buyer_assignments}')
        self.stdout.write(f'资料 uploader 重分配: {len(resources)}')
        self.stdout.write(f'资料订单 buyer/seller 重分配: {resource_order_buyer_assignments}')
        self.stdout.write('统计分析接口为实时聚合，无需额外刷新任务。')
