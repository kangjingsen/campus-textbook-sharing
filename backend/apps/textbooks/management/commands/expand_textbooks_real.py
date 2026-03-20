import json
import random
import re
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.textbooks.models import Category, Textbook, TextbookVote


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)

CN_QUERIES = [
    "大学生体质与健康", "高等数学", "大学英语", "计算机网络", "数据结构", "线性代数",
    "概率论", "经济学", "管理学", "会计学", "机械设计", "电路", "操作系统",
]

EN_QUERIES = [
    "data structures", "algorithms", "calculus", "linear algebra", "microeconomics",
    "macroeconomics", "computer networks", "operating systems", "database systems",
    "physics", "chemistry", "marketing", "management",
]

PUBLISHER_FALLBACK = [
    "高等教育出版社", "清华大学出版社", "机械工业出版社", "人民邮电出版社",
    "Pearson", "O'Reilly Media", "Springer", "MIT Press",
]


@dataclass
class Candidate:
    title: str
    author: str
    publisher: str
    isbn: str
    source: str


def normalize_title(title: str) -> str:
    if not title:
        return ""
    s = title.lower().strip()
    s = re.sub(r"[\s\-_—:：,，.。()（）\[\]{}'\"`~!@#$%^&*+/\\|<>?]+", "", s)
    return s


def fetch_json(url: str, timeout: int = 12) -> Optional[dict]:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except BaseException:
        # 网络抖动、源站拦截或中断时返回空，继续尝试其他来源
        return None


def fetch_html(url: str, timeout: int = 12) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except BaseException:
        # 网络抖动、源站拦截或中断时返回空，继续尝试其他来源
        return ""


def pick_owner(users):
    return random.choice(users)


def pick_category(categories):
    return random.choice(categories)


def infer_transaction_and_price():
    transaction_type = random.choices(["sell", "rent", "free"], weights=[7, 2, 1], k=1)[0]
    original_price = Decimal(str(round(random.uniform(25, 180), 2)))
    if transaction_type == "free":
        price = Decimal("0.00")
        rent_duration = None
    elif transaction_type == "rent":
        price = Decimal(str(round(float(original_price) * random.uniform(0.12, 0.28), 2)))
        rent_duration = random.choice([7, 14, 30, 60])
    else:
        price = Decimal(str(round(float(original_price) * random.uniform(0.35, 0.85), 2)))
        rent_duration = None
    return transaction_type, original_price, price, rent_duration


def yield_from_douban() -> Iterable[Candidate]:
    # 豆瓣建议接口（中文网站）
    for q in CN_QUERIES:
        url = f"https://book.douban.com/j/subject_suggest?q={quote(q)}"
        data = fetch_json(url)
        if not isinstance(data, list):
            continue
        for item in data:
            title = (item.get("title") or "").strip()
            if not title:
                continue
            author = (item.get("author_name") or "").strip() or "佚名"
            year = (item.get("year") or "").strip()
            publisher = f"豆瓣来源{(' ' + year) if year else ''}".strip()
            yield Candidate(
                title=title,
                author=author,
                publisher=publisher,
                isbn=(item.get("id") or ""),
                source="douban",
            )
        time.sleep(0.2)


def yield_from_openlibrary() -> Iterable[Candidate]:
    # OpenLibrary（海外网站）
    for q in EN_QUERIES + CN_QUERIES:
        for page in range(1, 5):
            url = f"https://openlibrary.org/search.json?q={quote(q)}&page={page}&limit=100"
            data = fetch_json(url)
            if not data:
                continue
            docs = data.get("docs", [])
            for d in docs:
                title = (d.get("title") or "").strip()
                if not title:
                    continue
                author_list = d.get("author_name") or []
                publisher_list = d.get("publisher") or []
                isbn_list = d.get("isbn") or []
                yield Candidate(
                    title=title,
                    author=(author_list[0] if author_list else "Unknown").strip(),
                    publisher=(publisher_list[0] if publisher_list else random.choice(PUBLISHER_FALLBACK)).strip(),
                    isbn=(isbn_list[0] if isbn_list else "").strip()[:20],
                    source="openlibrary",
                )
            time.sleep(0.2)


def yield_from_google_books() -> Iterable[Candidate]:
    # Google Books（海外网站）
    for q in EN_QUERIES + CN_QUERIES:
        for start in [0, 40, 80]:
            url = (
                "https://www.googleapis.com/books/v1/volumes"
                f"?q={quote(q)}&startIndex={start}&maxResults=40&printType=books"
            )
            data = fetch_json(url)
            if not data:
                continue
            for item in data.get("items", []):
                info = item.get("volumeInfo") or {}
                title = (info.get("title") or "").strip()
                if not title:
                    continue
                authors = info.get("authors") or []
                publishers = info.get("publisher") or ""
                identifiers = info.get("industryIdentifiers") or []
                isbn = ""
                if identifiers:
                    isbn = (identifiers[0].get("identifier") or "").strip()[:20]
                yield Candidate(
                    title=title,
                    author=(authors[0] if authors else "Unknown").strip(),
                    publisher=(publishers or random.choice(PUBLISHER_FALLBACK)).strip(),
                    isbn=isbn,
                    source="google_books",
                )
            time.sleep(0.2)


def yield_from_ireader() -> Iterable[Candidate]:
    # 掌阅（ireader）页面抓取，页面结构变化时会自动跳过
    for q in CN_QUERIES + EN_QUERIES[:5]:
        url = f"https://www.ireader.com/index.php?ca=search.index&keyword={quote(q)}"
        html = fetch_html(url)
        if not html:
            continue

        # 兜底正则，尽量抓 title/author 信息
        pattern = re.compile(
            r'title="(?P<title>[^"<>]{2,120})"[^>]*>\s*</a>.*?author[^>]*>\s*(?P<author>[^<]{1,80})',
            re.IGNORECASE | re.DOTALL,
        )
        for m in pattern.finditer(html):
            title = (m.group("title") or "").strip()
            author = (m.group("author") or "").strip() or "佚名"
            if not title:
                continue
            yield Candidate(
                title=title,
                author=author,
                publisher="掌阅来源",
                isbn="",
                source="ireader",
            )
        time.sleep(0.2)


def yield_from_fanqie() -> Iterable[Candidate]:
    # 番茄免费小说页面抓取，页面结构变化时会自动跳过
    for q in CN_QUERIES:
        url = f"https://fanqienovel.com/search/{quote(q)}"
        html = fetch_html(url)
        if not html:
            continue

        # 兜底正则，尽量抓 title/author 信息
        pattern = re.compile(
            r'"book_name"\s*:\s*"(?P<title>[^"]{2,120})".*?"author"\s*:\s*"(?P<author>[^"]{1,80})"',
            re.IGNORECASE | re.DOTALL,
        )
        for m in pattern.finditer(html):
            title = (m.group("title") or "").strip()
            author = (m.group("author") or "").strip() or "佚名"
            if not title:
                continue
            yield Candidate(
                title=title,
                author=author,
                publisher="番茄来源",
                isbn="",
                source="fanqie",
            )
        time.sleep(0.2)


def add_votes_for_textbook(textbook: Textbook, users: List) -> None:
    """为新增教材注入点赞/点踩交互数据。"""
    candidates = [u for u in users if u.id != textbook.owner_id]
    if not candidates:
        return

    random.shuffle(candidates)
    # 小规模样本，避免刷票过重
    vote_n = random.randint(0, min(6, len(candidates)))
    selected = candidates[:vote_n]

    for u in selected:
        vote = 1 if random.random() < 0.82 else -1
        TextbookVote.objects.update_or_create(
            textbook=textbook,
            user=u,
            defaults={"vote": vote},
        )


class Command(BaseCommand):
    help = "抓取真实书籍信息并扩容教材总量（默认扩展为当前总量的4倍）"

    def add_arguments(self, parser):
        parser.add_argument("--multiplier", type=int, default=4, help="目标倍数，默认4")
        parser.add_argument("--target-total", type=int, default=0, help="目标总量（优先级高于 multiplier）")
        parser.add_argument("--owner-username", type=str, default="admin", help="新增教材归属用户名，默认 admin")
        parser.add_argument("--dry-run", action="store_true", help="仅预览不写入")

    def handle(self, *args, **options):
        multiplier = max(2, int(options["multiplier"]))
        target_total_opt = int(options["target_total"] or 0)
        owner_username = (options.get("owner_username") or "admin").strip()
        dry_run = bool(options["dry_run"])

        current_total = Textbook.objects.count()
        target_total = target_total_opt if target_total_opt > 0 else current_total * multiplier
        need = target_total - current_total

        if need <= 0:
            self.stdout.write(self.style.WARNING("当前总量已达到目标，无需扩容。"))
            return

        categories = list(Category.objects.filter(is_active=True))
        if not categories:
            self.stdout.write(self.style.ERROR("未找到分类，无法创建教材。"))
            return

        User = get_user_model()
        all_users = list(User.objects.filter(is_active=True))
        if not all_users:
            self.stdout.write(self.style.ERROR("未找到可用用户，无法创建教材。"))
            return

        owner = User.objects.filter(username=owner_username, is_active=True).first()
        if owner is None:
            owner = User.objects.filter(username="admin", is_active=True).first() or all_users[0]

        existing_norm = set(normalize_title(t) for t in Textbook.objects.values_list("title", flat=True))
        staged_norm = set()
        candidates: List[Candidate] = []

        self.stdout.write(f"当前教材总量: {current_total}")
        self.stdout.write(f"目标教材总量: {target_total}")
        self.stdout.write(f"需要新增: {need}")

        # 聚合多源真实书名（按来源配额，确保中外来源均覆盖）
        target_pool = need * 2
        source_defs = [
            ("douban", yield_from_douban(), max(80, target_pool // 5)),
            ("ireader", yield_from_ireader(), max(40, target_pool // 10)),
            ("fanqie", yield_from_fanqie(), max(40, target_pool // 10)),
            ("openlibrary", yield_from_openlibrary(), max(120, target_pool // 2)),
            ("google_books", yield_from_google_books(), max(120, target_pool // 2)),
        ]

        for source_name, source_iter, quota in source_defs:
            grabbed = 0
            for c in source_iter:
                nt = normalize_title(c.title)
                if not nt:
                    continue
                if nt in existing_norm or nt in staged_norm:
                    continue
                staged_norm.add(nt)
                candidates.append(c)
                grabbed += 1
                if grabbed >= quota or len(candidates) >= target_pool:
                    break
            self.stdout.write(f"来源 {source_name} 抓取有效候选: {grabbed}")
            if len(candidates) >= target_pool:
                break

        if not candidates:
            self.stdout.write(self.style.ERROR("未抓取到可用书籍数据，请重试。"))
            return

        random.shuffle(candidates)
        chosen = candidates[:need]

        self.stdout.write(f"可用候选数: {len(candidates)}")
        self.stdout.write(f"计划入库数: {len(chosen)}")

        if dry_run:
            for c in chosen[:20]:
                self.stdout.write(f"[DRY] {c.title} | {c.author} | {c.source}")
            return

        created = 0
        for c in chosen:
            transaction_type, original_price, price, rent_duration = infer_transaction_and_price()
            category = pick_category(categories)

            title = c.title[:200]
            author = (c.author or "Unknown")[:200]
            publisher = (c.publisher or random.choice(PUBLISHER_FALLBACK))[:200]
            isbn = (c.isbn or "")[:20]

            if Textbook.objects.filter(title=title).exists():
                # 最终落库前再去重一次
                continue

            textbook = Textbook.objects.create(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                edition=random.choice(["第1版", "第2版", "第3版"]),
                condition=random.choice([5, 4, 4, 3, 3, 2]),
                description=f"[REAL_WEB_{c.source}] 基于公开网页抓取的真实书籍信息。",
                price=price,
                original_price=original_price,
                transaction_type=transaction_type,
                rent_duration=rent_duration,
                category=category,
                owner=owner,
                status="approved",
                view_count=random.randint(20, 1200),
            )
            add_votes_for_textbook(textbook, all_users)
            created += 1

        final_total = Textbook.objects.count()
        self.stdout.write(self.style.SUCCESS(f"新增完成: {created} 本"))
        self.stdout.write(self.style.SUCCESS(f"扩容后总量: {final_total}"))
