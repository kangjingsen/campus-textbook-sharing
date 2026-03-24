from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '创建 user1-user20 账号，密码为用户名+123456（例如 user1 的密码是 user1123456）'

    def add_arguments(self, parser):
        parser.add_argument('--start', type=int, default=1, help='起始编号，默认 1')
        parser.add_argument('--end', type=int, default=20, help='结束编号，默认 20')

    def handle(self, *args, **options):
        start = int(options['start'])
        end = int(options['end'])
        if start <= 0 or end < start:
            self.stdout.write(self.style.ERROR('参数非法：请保证 start >= 1 且 end >= start'))
            return

        User = get_user_model()
        created = 0
        existing = 0

        for idx in range(start, end + 1):
            username = f'user{idx}'
            password = f'{username}123456'

            if User.objects.filter(username=username).exists():
                existing += 1
                continue

            User.objects.create_user(
                username=username,
                password=password,
                role='student',
                is_active=True,
                is_verified=True,
                email=f'{username}@example.com',
                student_id=f'S{idx:06d}',
                college='测试学院',
                major='测试专业'
            )
            created += 1

        self.stdout.write(self.style.SUCCESS('用户创建命令执行完成'))
        self.stdout.write(f'新增用户: {created}')
        self.stdout.write(f'已存在跳过: {existing}')
