from django.core.management.base import BaseCommand

from apps.textbooks.cover_utils import ensure_textbook_cover
from apps.textbooks.models import Textbook


class Command(BaseCommand):
    help = '检查教材封面：先自动匹配，再尝试在线获取，最后自动生成封面。'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='最多处理多少条，0 表示全部')
        parser.add_argument('--dry-run', action='store_true', help='仅统计，不真正写入')
        parser.add_argument('--no-online', action='store_true', help='跳过在线 ISBN 封面拉取')

    def handle(self, *args, **options):
        limit = max(0, int(options.get('limit') or 0))
        dry_run = bool(options.get('dry_run'))
        no_online = bool(options.get('no_online'))

        qs = Textbook.objects.filter(cover_image='') | Textbook.objects.filter(cover_image__isnull=True)
        qs = qs.order_by('id')
        if limit > 0:
            qs = qs[:limit]

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('所有教材都已有封面，无需处理。'))
            return

        self.stdout.write(f'准备处理 {total} 本教材（dry_run={dry_run}, online={not no_online}）')

        stats = {
            'matched_isbn': 0,
            'matched_title': 0,
            'online_isbn': 0,
            'generated': 0,
            'failed': 0,
            'exists': 0,
        }

        def safe_text(value: str, limit: int = 24) -> str:
            text = (value or '')[:limit]
            # 避免 Windows GBK 终端在输出特殊字符时抛出编码异常。
            return text.encode('gbk', errors='replace').decode('gbk', errors='replace')

        for textbook in qs:
            if dry_run:
                self.stdout.write(f'[DRY] #{textbook.id} {safe_text(textbook.title, limit=60)}')
                continue

            result = ensure_textbook_cover(textbook, try_online=not no_online)
            stats[result] = stats.get(result, 0) + 1
            self.stdout.write(f'#{textbook.id} {safe_text(textbook.title)} -> {result}')

        if dry_run:
            self.stdout.write(self.style.SUCCESS('dry-run 完成（未写入）。'))
            return

        summary = ', '.join(f'{k}={v}' for k, v in stats.items() if v)
        self.stdout.write(self.style.SUCCESS(f'处理完成：{summary or "无变更"}'))