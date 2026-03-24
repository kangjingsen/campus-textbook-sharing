import json
import random
import re
import ssl
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.textbooks.models import Category, Textbook


SSL_CONTEXT = ssl.create_default_context()
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36'
)

QUERY_TOPICS = [
    '高等数学', '线性代数', '概率论与数理统计', '离散数学', '大学物理', '有机化学', '无机化学',
    '数据结构', '操作系统', '计算机网络', '数据库系统', '编程语言', '人工智能', '机器学习',
    '经济学原理', '微观经济学', '宏观经济学', '管理学', '会计学', '金融学', '市场营销',
    '法学概论', '民法学', '中国史', '世界史', '哲学导论', '现代汉语', '中国文学', '大学英语',
    '机械设计', '电子信息工程', '通信原理', '土木工程材料', '医学基础', '解剖学'
]

BROADEN_TOPICS = [
    '中国', '教材', '课程', '大学', '高校', '社会科学', '自然科学', '工程', '管理', '经济',
    '法律', '历史', '文学', '语言', '数学', '物理', '化学', '计算机', '信息技术', '医学'
]

CATEGORY_KEYWORDS = {
    '数据结构': ['数据结构'],
    '操作系统': ['操作系统'],
    '计算机网络': ['计算机网络', '网络安全', '网络协议'],
    '数据库': ['数据库', 'sql', '数据仓库'],
    '编程语言': ['编程', '程序设计', 'java', 'python', 'c语言', 'c++'],
    '人工智能': ['人工智能', '机器学习', '深度学习', '神经网络'],
    '高等数学': ['高等数学', '微积分'],
    '线性代数': ['线性代数', '矩阵'],
    '概率统计': ['概率论', '数理统计', '统计学'],
    '数学': ['数学分析', '离散数学'],
    '物理': ['物理', '力学', '电磁学', '热学'],
    '化学': ['化学', '有机化学', '无机化学', '物理化学'],
    '经济学': ['经济学', '宏观经济', '微观经济'],
    '管理学': ['管理学', '管理'],
    '会计学': ['会计', '审计', '财务'],
    '金融学': ['金融', '投资', '证券', '银行学'],
    '法学': ['法学', '法律', '民法', '刑法'],
    '历史': ['历史', '中国史', '世界史'],
    '哲学': ['哲学', '伦理学', '逻辑学'],
    '中文': ['中文', '汉语', '文学', '写作'],
    '英语': ['英语', '英汉', '翻译', '听力'],
    '机械工程': ['机械', '机械设计'],
    '电子信息': ['电子', '通信', '信号'],
    '土木工程': ['土木', '工程材料', '工程力学'],
    '医学': ['医学', '解剖', '病理', '药理'],
}


@dataclass
class Candidate:
    title: str
    author: str
    publisher: str
    cover_url: str
    source: str


def is_chinese_title(title: str) -> bool:
    text = title or ''
    han_count = len(re.findall(r'[\u4e00-\u9fff]', text))
    kana_count = len(re.findall(r'[\u3040-\u30ff]', text))
    # 仅保留以汉字为主且不含日文假名的标题（兼容简体/繁体中文）。
    return han_count >= 2 and kana_count == 0


def normalize_title(title: str) -> str:
    text = (title or '').strip().lower()
    text = re.sub(r'[\s\-_:：,，.。()（）\[\]{}]+', '', text)
    return text


def fetch_json(url: str, timeout: int = 12):
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode('utf-8', errors='ignore'))


def fetch_image(url: str, timeout: int = 15) -> bytes:
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
        ctype = (resp.headers.get('Content-Type') or '').lower()
        body = resp.read()
    if 'image' not in ctype:
        return b''
    return body


def safe_fetch_json(url: str):
    try:
        return fetch_json(url)
    except BaseException:
        return None


def safe_fetch_image(url: str):
    try:
        return fetch_image(url)
    except BaseException:
        return b''


def from_douban(topic: str) -> List[Candidate]:
    url = f'https://book.douban.com/j/subject_suggest?q={quote(topic)}'
    data = safe_fetch_json(url)
    if not isinstance(data, list):
        return []

    result = []
    for item in data:
        title = (item.get('title') or '').strip()
        if not is_chinese_title(title):
            continue
        author = (item.get('author_name') or '').strip()
        cover = (item.get('cover') or item.get('img') or item.get('pic') or '').strip()
        if cover.startswith('http://'):
            cover = 'https://' + cover[len('http://'):]
        result.append(Candidate(
            title=title,
            author=author,
            publisher='',
            cover_url=cover,
            source='douban'
        ))
    return result


def from_google_books(topic: str) -> List[Candidate]:
    url = (
        'https://www.googleapis.com/books/v1/volumes'
        f'?q={quote(topic)}&maxResults=30&langRestrict=zh&printType=books'
    )
    data = safe_fetch_json(url)
    if not isinstance(data, dict):
        return []

    result = []
    for item in (data.get('items') or []):
        info = item.get('volumeInfo') or {}
        title = (info.get('title') or '').strip()
        if not is_chinese_title(title):
            continue
        authors = info.get('authors') or []
        publisher = (info.get('publisher') or '').strip()
        links = info.get('imageLinks') or {}
        cover = links.get('thumbnail') or links.get('smallThumbnail') or ''
        if cover.startswith('http://'):
            cover = 'https://' + cover[len('http://'):]
        result.append(Candidate(
            title=title,
            author=(authors[0] if authors else '').strip(),
            publisher=publisher,
            cover_url=cover,
            source='google_books'
        ))
    return result


def pick_category(title: str, category_lookup: Dict[str, Category]) -> Optional[Category]:
    text = title or ''
    score = {}
    for cname, keywords in CATEGORY_KEYWORDS.items():
        if cname not in category_lookup:
            continue
        val = 0
        for kw in keywords:
            if kw in text:
                val += 2 + min(3, len(kw) // 4)
        if val > 0:
            score[cname] = val

    if score:
        target = sorted(score.items(), key=lambda x: x[1], reverse=True)[0][0]
        return category_lookup[target]

    for fallback in ['中文', '经济学', '管理学', '高等数学', '计算机科学', '理工科']:
        if fallback in category_lookup:
            return category_lookup[fallback]
    return None


def transaction_and_price() -> tuple:
    transaction_type = random.choices(['sell', 'rent', 'free'], weights=[7, 2, 1], k=1)[0]
    original_price = Decimal(str(round(random.uniform(20, 150), 2)))
    if transaction_type == 'free':
        price = Decimal('0.00')
        rent_duration = None
    elif transaction_type == 'rent':
        price = Decimal(str(round(float(original_price) * random.uniform(0.12, 0.28), 2)))
        rent_duration = random.choice([7, 14, 30, 60])
    else:
        price = Decimal(str(round(float(original_price) * random.uniform(0.35, 0.8), 2)))
        rent_duration = None
    return transaction_type, original_price, price, rent_duration


class Command(BaseCommand):
    help = '从公开网站抓取中文书籍（真实封面）并入库，支持按四个用户轮转分配。'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=500, help='新增目标数量，默认500')
        parser.add_argument('--owners', type=str, default='', help='逗号分隔用户名（最多前4个），为空自动选4人')
        parser.add_argument('--sleep-ms', type=int, default=120, help='请求间隔毫秒，默认120')
        parser.add_argument('--dry-run', action='store_true', help='仅预览，不写库')
        parser.add_argument('--broaden', action='store_true', help='扩展查询词范围，提升在限流场景下的命中率')

    def handle(self, *args, **options):
        target = max(1, int(options['count']))
        owners_arg = (options.get('owners') or '').strip()
        sleep_ms = max(0, int(options['sleep_ms']))
        dry_run = bool(options['dry_run'])
        broaden = bool(options['broaden'])

        User = get_user_model()
        if owners_arg:
            usernames = [x.strip() for x in owners_arg.split(',') if x.strip()]
            owners = list(User.objects.filter(username__in=usernames, is_active=True).order_by('id')[:4])
        else:
            owners = list(User.objects.filter(is_active=True).order_by('id')[:4])

        if len(owners) < 4:
            self.stdout.write(self.style.ERROR('可用用户不足4个，无法按四人分配。'))
            return

        categories = list(Category.objects.filter(is_active=True))
        if not categories:
            self.stdout.write(self.style.ERROR('没有可用分类。'))
            return

        category_lookup = {}
        grouped: Dict[str, List[Category]] = {}
        for c in categories:
            grouped.setdefault(c.name, []).append(c)
        for name, items in grouped.items():
            items = sorted(items, key=lambda x: (x.level, x.id), reverse=True)
            category_lookup[name] = items[0]

        existing = set(normalize_title(t) for t in Textbook.objects.values_list('title', flat=True))
        staged = set()

        created = 0
        cover_ok = 0
        owner_idx = 0
        attempts = 0
        max_attempts = target * 30

        topic_pool = QUERY_TOPICS + BROADEN_TOPICS if broaden else QUERY_TOPICS

        self.stdout.write(f'目标新增: {target}，四人分配: {[u.username for u in owners]}，dry_run={dry_run}，broaden={broaden}')

        while created < target and attempts < max_attempts:
            topic = random.choice(topic_pool)
            source_data = []
            source_data.extend(from_douban(topic))
            source_data.extend(from_google_books(topic))
            random.shuffle(source_data)

            for candidate in source_data:
                attempts += 1
                nt = normalize_title(candidate.title)
                if not nt or nt in existing or nt in staged:
                    continue
                if not candidate.cover_url:
                    continue

                image_bytes = safe_fetch_image(candidate.cover_url)
                if len(image_bytes) < 1500:
                    continue

                owner = owners[owner_idx % 4]
                owner_idx += 1
                category = pick_category(candidate.title, category_lookup)
                transaction_type, original_price, price, rent_duration = transaction_and_price()

                staged.add(nt)
                if dry_run:
                    created += 1
                    cover_ok += 1
                    if created <= 20 or created % 100 == 0:
                        self.stdout.write(f'[DRY {created}/{target}] {candidate.title} -> {owner.username} / {(category.name if category else "未分类")}')
                else:
                    textbook = Textbook.objects.create(
                        title=candidate.title[:200],
                        author=(candidate.author or '佚名')[:200],
                        isbn='',
                        publisher=(candidate.publisher or '公开数据来源')[:200],
                        edition=random.choice(['第1版', '第2版', '第3版']),
                        condition=random.choice([5, 4, 4, 3, 3, 2]),
                        description=f'[REAL_CN_WEB:{candidate.source}] 中文书籍公开来源入库。',
                        price=price,
                        original_price=original_price,
                        transaction_type=transaction_type,
                        rent_duration=rent_duration,
                        category=category,
                        owner=owner,
                        status='approved',
                        view_count=random.randint(20, 980),
                    )
                    textbook.cover_image.save(f'real_cn_{textbook.id}.jpg', ContentFile(image_bytes), save=True)
                    created += 1
                    cover_ok += 1
                    if created <= 20 or created % 100 == 0:
                        self.stdout.write(f'[{created}/{target}] #{textbook.id} {candidate.title[:36]} -> {owner.username} / {(category.name if category else "未分类")}')

                if sleep_ms:
                    time.sleep(sleep_ms / 1000)

                if created >= target:
                    break

            if sleep_ms:
                time.sleep(sleep_ms / 1000)

        if created < target:
            self.stdout.write(self.style.WARNING(f'仅完成 {created}/{target}，可能受限于外部站点限流或可用数据不足。'))

        self.stdout.write(self.style.SUCCESS(f'完成: 新增 {created} 本，真实封面 {cover_ok} 本。'))
        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run 模式未写入数据库。'))
