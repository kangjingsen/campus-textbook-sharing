from django.core.management.base import BaseCommand
from django.db import transaction

from apps.orders.models import Order
from apps.textbooks.models import Textbook, ResourceOrder


class Command(BaseCommand):
    help = '回填历史订单取消原因/取消方，并按历史完成或取消订单修正教材状态。'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='仅预览，不写库')

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = bool(options.get('dry_run'))

        # 1) 回填历史取消订单字段
        tb_reason_qs = Order.objects.filter(status='cancelled', cancel_reason='')
        tb_role_qs = Order.objects.filter(status='cancelled', cancel_by_role='')
        res_reason_qs = ResourceOrder.objects.filter(status='cancelled', cancel_reason='')
        res_role_qs = ResourceOrder.objects.filter(status='cancelled', cancel_by_role='')

        tb_reason_count = tb_reason_qs.count()
        tb_role_count = tb_role_qs.count()
        res_reason_count = res_reason_qs.count()
        res_role_count = res_role_qs.count()

        if not dry_run:
            if tb_reason_count:
                tb_reason_qs.update(cancel_reason='other')
            if tb_role_count:
                tb_role_qs.update(cancel_by_role='system')
            if res_reason_count:
                res_reason_qs.update(cancel_reason='other')
            if res_role_count:
                res_role_qs.update(cancel_by_role='system')

        # 2) 适配历史完成/取消订单后的教材状态
        status_changed = 0
        reviewed = 0
        textbooks = Textbook.objects.all().only('id', 'status', 'transaction_type')
        for tb in textbooks.iterator():
            reviewed += 1
            orders = Order.objects.filter(textbook_id=tb.id)
            has_active = orders.filter(status__in=['pending', 'confirmed']).exists()
            has_completed = orders.filter(status='completed').exists()

            target_status = tb.status
            if has_active:
                target_status = 'rented' if tb.transaction_type == 'rent' else 'sold'
            elif tb.transaction_type == 'rent' and has_completed:
                # 租赁完成但未归还时保持已租出
                target_status = 'rented'
            elif tb.transaction_type != 'rent' and has_completed:
                target_status = 'sold'
            elif tb.status in ['sold', 'rented']:
                # 没有进行中也没有完成订单，回到可上架
                target_status = 'approved'

            if target_status != tb.status:
                status_changed += 1
                if not dry_run:
                    Textbook.objects.filter(pk=tb.id).update(status=target_status)

        self.stdout.write(
            f'历史取消订单回填: 教材原因 {tb_reason_count}，教材取消方 {tb_role_count}，'
            f'资料原因 {res_reason_count}，资料取消方 {res_role_count}'
        )
        self.stdout.write(f'教材状态适配: 扫描 {reviewed} 本，变更 {status_changed} 本')

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run 模式未写入数据库，事务已回滚。'))
            transaction.set_rollback(True)
        else:
            self.stdout.write(self.style.SUCCESS('历史订单适配完成。'))
