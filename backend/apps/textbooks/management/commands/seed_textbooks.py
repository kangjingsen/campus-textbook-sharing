import io
import random
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.textbooks.models import Category, Textbook

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None
    ImageDraw = None


PUBLISHERS = [
    '高等教育出版社', '清华大学出版社', '机械工业出版社', '人民邮电出版社',
    '电子工业出版社', '北京大学出版社', '复旦大学出版社', '中国人民大学出版社'
]

AUTHORS = [
    '张伟', '王芳', '李娜', '刘洋', '陈杰', '杨磊', '赵敏', '周倩', '黄涛', '吴迪'
]

EDITION_POOL = ['第1版', '第2版', '第3版', '第4版']


def generate_isbn(seed_num: int) -> str:
    core = f"9787{seed_num:09d}"[:12]
    checksum = sum((i + 1) * int(c) for i, c in enumerate(core)) % 10
    return f"{core}{checksum}"


def make_cover_image(title: str, category_name: str, color_seed: int) -> ContentFile:
    if Image is None:
        return ContentFile(b'', name='cover.jpg')

    random.seed(color_seed)
    bg = (random.randint(60, 180), random.randint(80, 190), random.randint(90, 200))
    fg = (245, 245, 245)

    image = Image.new('RGB', (600, 800), bg)
    draw = ImageDraw.Draw(image)

    draw.rectangle((30, 30, 570, 770), outline=(255, 255, 255), width=4)
    draw.text((50, 80), 'Campus Textbook', fill=fg)
    draw.text((50, 130), f'Category: {category_name[:24]}', fill=fg)
    draw.text((50, 200), title[:28], fill=fg)

    bio = io.BytesIO()
    image.save(bio, format='JPEG', quality=88)
    return ContentFile(bio.getvalue(), name='cover.jpg')


class Command(BaseCommand):
    help = '按末级分类补充教材数据（默认每个分类补到10本）'

    def add_arguments(self, parser):
        parser.add_argument('--per-category', type=int, default=10, help='每个末级分类目标数量，默认10')
        parser.add_argument('--only-empty', action='store_true', help='仅填充当前没有教材的分类')

    def handle(self, *args, **options):
        per_category = max(1, int(options['per_category']))
        only_empty = bool(options['only_empty'])

        User = get_user_model()
        owner = User.objects.filter(is_active=True, role='student').first() or User.objects.filter(is_active=True).first()
        if not owner:
            self.stdout.write(self.style.ERROR('未找到可用用户，请先创建用户后再执行。'))
            return

        leaf_categories = Category.objects.filter(is_active=True, children__isnull=True).distinct().order_by('id')
        if not leaf_categories.exists():
            self.stdout.write(self.style.WARNING('未找到末级分类（leaf categories），未生成数据。'))
            return

        created_total = 0
        for category in leaf_categories:
            existing_count = Textbook.objects.filter(category=category).count()
            if only_empty and existing_count > 0:
                continue

            need = max(0, per_category - existing_count)
            if need == 0:
                continue

            for idx in range(1, need + 1):
                serial = existing_count + idx
                title = f"{category.name}学习指南 {serial}"
                while Textbook.objects.filter(category=category, title=title).exists():
                    serial += 1
                    title = f"{category.name}学习指南 {serial}"

                author = random.choice(AUTHORS)
                transaction_type = random.choices(['sell', 'rent', 'free'], weights=[7, 2, 1], k=1)[0]
                condition = random.choice([5, 4, 4, 3, 3, 2])

                original_price = Decimal(str(round(random.uniform(30, 120), 2)))
                if transaction_type == 'free':
                    price = Decimal('0.00')
                elif transaction_type == 'rent':
                    price = Decimal(str(round(float(original_price) * random.uniform(0.12, 0.28), 2)))
                else:
                    price = Decimal(str(round(float(original_price) * random.uniform(0.35, 0.75), 2)))

                textbook = Textbook.objects.create(
                    title=title,
                    author=author,
                    isbn=generate_isbn(category.id * 1000 + serial),
                    publisher=random.choice(PUBLISHERS),
                    edition=random.choice(EDITION_POOL),
                    condition=condition,
                    description=f"[AUTO_SEED] {category.name} 课程配套教材，内容完整，适合复习与备考。",
                    price=price,
                    original_price=original_price,
                    transaction_type=transaction_type,
                    rent_duration=(random.choice([7, 14, 30, 60]) if transaction_type == 'rent' else None),
                    category=category,
                    owner=owner,
                    status='approved',
                    view_count=random.randint(5, 220),
                )

                if Image is not None:
                    cover = make_cover_image(title, category.name, category.id * 10000 + serial)
                    textbook.cover_image.save(f"seeded_{category.id}_{serial}.jpg", cover, save=True)

                created_total += 1

            self.stdout.write(self.style.SUCCESS(f"分类「{category.name}」补充 {need} 本（现有 {existing_count + need}/{per_category}+）"))

        self.stdout.write(self.style.SUCCESS(f"完成：共新增 {created_total} 本教材。"))
