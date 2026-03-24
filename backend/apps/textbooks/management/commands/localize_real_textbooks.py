import json
import re
import ssl
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.textbooks.models import Textbook


SSL_CONTEXT = ssl.create_default_context()
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36'
)


@dataclass
class MetadataCandidate:
    title: str
    author: str
    publisher: str
    cover_url: str
    source: str


def fetch_json(url: str, timeout: int = 12):
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode('utf-8', errors='ignore'))


def fetch_bytes(url: str, timeout: int = 15) -> bytes:
    req = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
        content_type = (resp.headers.get('Content-Type') or '').lower()
        body = resp.read()
    if 'image' not in content_type:
        return b''
    return body


def normalize_isbn(value: str) -> str:
    if not value:
        return ''
    normalized = ''.join(ch for ch in value if ch.isdigit() or ch.upper() == 'X')
    return normalized if len(normalized) in (10, 13) else ''


def is_chinese_text(value: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', value or ''))


def is_english_dominant(value: str) -> bool:
    text = value or ''
    english = sum(1 for ch in text if ('A' <= ch <= 'Z') or ('a' <= ch <= 'z'))
    chinese = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    return english >= 6 and english > chinese * 2


def normalize_title_for_query(title: str) -> str:
    if not title:
        return ''
    text = re.sub(r'\(.*?\)|（.*?）', ' ', title)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:80]


def query_google_books(query: str, zh_only: bool = True) -> List[MetadataCandidate]:
    if not query:
        return []

    lang_part = '&langRestrict=zh' if zh_only else ''
    url = (
        'https://www.googleapis.com/books/v1/volumes'
        f'?q={quote(query)}&maxResults=5&printType=books{lang_part}'
    )
    data = fetch_json(url)
    items = data.get('items') or []
    results: List[MetadataCandidate] = []

    for item in items:
        info = item.get('volumeInfo') or {}
        title = (info.get('title') or '').strip()
        authors = info.get('authors') or []
        publisher = (info.get('publisher') or '').strip()

        image_links = info.get('imageLinks') or {}
        cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail') or ''
        if cover_url.startswith('http://'):
            cover_url = 'https://' + cover_url[len('http://'):]

        results.append(MetadataCandidate(
            title=title,
            author=(authors[0] if authors else '').strip(),
            publisher=publisher,
            cover_url=cover_url,
            source='google_books'
        ))

    return results


def query_douban_suggest(query: str) -> List[MetadataCandidate]:
    if not query:
        return []

    url = f'https://book.douban.com/j/subject_suggest?q={quote(query)}'
    data = fetch_json(url)
    if not isinstance(data, list):
        return []

    results: List[MetadataCandidate] = []
    for item in data[:8]:
        title = (item.get('title') or '').strip()
        author = (item.get('author_name') or '').strip()
        cover_url = (item.get('cover') or item.get('img') or item.get('pic') or '').strip()
        if cover_url.startswith('http://'):
            cover_url = 'https://' + cover_url[len('http://'):]
        results.append(MetadataCandidate(
            title=title,
            author=author,
            publisher='',
            cover_url=cover_url,
            source='douban'
        ))
    return results


def query_openlibrary_cover_by_isbn(isbn: str) -> Optional[str]:
    normalized = normalize_isbn(isbn)
    if not normalized:
        return None
    return f'https://covers.openlibrary.org/b/isbn/{normalized}-L.jpg?default=false'


def safe_google_query(query: str, zh_only: bool = True) -> List[MetadataCandidate]:
    try:
        return query_google_books(query, zh_only=zh_only)
    except BaseException:
        return []


def safe_douban_query(query: str) -> List[MetadataCandidate]:
    try:
        return query_douban_suggest(query)
    except BaseException:
        return []


def score_candidate(candidate: MetadataCandidate) -> int:
    score = 0
    if is_chinese_text(candidate.title):
        score += 6
    if candidate.cover_url:
        score += 3
    if candidate.author and is_chinese_text(candidate.author):
        score += 2
    if candidate.publisher and is_chinese_text(candidate.publisher):
        score += 1
    return score


def dedupe_candidates(candidates: List[MetadataCandidate]) -> List[MetadataCandidate]:
    seen = set()
    result = []
    for c in candidates:
        key = (c.title.strip().lower(), c.author.strip().lower(), c.source)
        if key in seen:
            continue
        seen.add(key)
        result.append(c)
    return result


class Command(BaseCommand):
    help = '将 REAL_WEB 扩展书籍尽量替换为中文元数据，并从公开网站补齐真实书籍封面。'

    def add_arguments(self, parser):
        parser.add_argument('--scope', type=str, default='real-web', choices=['real-web', 'all'], help='处理范围')
        parser.add_argument('--limit', type=int, default=0, help='最多处理条数，0 表示全部')
        parser.add_argument('--dry-run', action='store_true', help='仅预览，不写入')
        parser.add_argument('--sleep-ms', type=int, default=120, help='每条请求间隔毫秒，默认 120')
        parser.add_argument('--include-covered', action='store_true', help='包含已有封面的教材')
        parser.add_argument('--include-non-english', action='store_true', help='包含非英文主导标题的教材')

    def handle(self, *args, **options):
        scope = options['scope']
        limit = max(0, int(options['limit']))
        dry_run = bool(options['dry_run'])
        sleep_ms = max(0, int(options['sleep_ms']))
        include_covered = bool(options['include_covered'])
        include_non_english = bool(options['include_non_english'])

        queryset = Textbook.objects.all().order_by('id')
        if scope == 'real-web':
            queryset = queryset.filter(description__startswith='[REAL_WEB_')

        candidates = []
        for textbook in queryset.iterator():
            if (not include_covered) and textbook.cover_image:
                continue
            if (not include_non_english) and (not is_english_dominant(textbook.title)):
                continue
            candidates.append(textbook)

        if limit > 0:
            candidates = candidates[:limit]

        total = len(candidates)
        self.stdout.write(f'待处理: {total} 本（scope={scope}, dry_run={dry_run}）')
        if total == 0:
            self.stdout.write(self.style.WARNING('没有符合条件的数据。'))
            return

        updated_count = 0
        title_updated_count = 0
        cover_updated_count = 0
        skipped_count = 0
        errors = 0

        for idx, textbook in enumerate(candidates, start=1):
            try:
                isbn = normalize_isbn(textbook.isbn)
                query_title = normalize_title_for_query(textbook.title)

                source_candidates: List[MetadataCandidate] = []

                if isbn:
                    source_candidates.extend(safe_google_query(f'isbn:{isbn}', zh_only=True))
                    source_candidates.extend(safe_douban_query(isbn))

                source_candidates.extend(safe_google_query(f'intitle:{query_title}', zh_only=True))
                source_candidates.extend(safe_douban_query(query_title))

                source_candidates = dedupe_candidates(source_candidates)
                source_candidates.sort(key=score_candidate, reverse=True)

                chosen_cn = None
                chosen_cover_url = ''
                for candidate in source_candidates:
                    if not chosen_cover_url and candidate.cover_url:
                        chosen_cover_url = candidate.cover_url
                    if chosen_cn is None and is_chinese_text(candidate.title):
                        chosen_cn = candidate
                    if chosen_cn and chosen_cover_url:
                        break

                if not chosen_cover_url and isbn:
                    fallback = query_openlibrary_cover_by_isbn(isbn)
                    if fallback:
                        chosen_cover_url = fallback

                changed = False
                title_changed = False
                cover_changed = False
                if chosen_cn and is_english_dominant(textbook.title):
                    textbook.title = chosen_cn.title[:200]
                    if chosen_cn.author:
                        textbook.author = chosen_cn.author[:200]
                    if chosen_cn.publisher:
                        textbook.publisher = chosen_cn.publisher[:200]
                    textbook.description = f'[REAL_WEB_CN:{chosen_cn.source}] 已从公开网站补齐中文元数据。'
                    changed = True
                    title_changed = True

                if chosen_cover_url and (not textbook.cover_image):
                    image_bytes = fetch_bytes(chosen_cover_url)
                    if len(image_bytes) >= 1500:
                        file_name = f'real_cover_{textbook.id}.jpg'
                        textbook.cover_image.save(file_name, ContentFile(image_bytes), save=False)
                        changed = True
                        cover_changed = True

                if changed:
                    updated_count += 1
                    if not dry_run:
                        textbook.save()
                    if title_changed:
                        title_updated_count += 1
                    if cover_changed:
                        cover_updated_count += 1
                    if idx <= 10 or idx % 100 == 0:
                        self.stdout.write(f'[{idx}/{total}] 更新 #{textbook.id}: {textbook.title[:36]}')
                else:
                    skipped_count += 1

                if sleep_ms:
                    time.sleep(sleep_ms / 1000.0)

            except BaseException as exc:
                errors += 1
                self.stdout.write(self.style.WARNING(f'[{idx}/{total}] 处理失败 #{textbook.id}: {exc}'))

        self.stdout.write(self.style.SUCCESS(
            f'完成: 总计 {total}，更新 {updated_count}（标题 {title_updated_count}，封面 {cover_updated_count}），跳过 {skipped_count}，失败 {errors}'
        ))
        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run 模式未写入数据库。'))
