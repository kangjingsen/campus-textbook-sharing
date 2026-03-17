import json
import re
import ssl
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.textbooks.models import Textbook


SSL_CONTEXT = ssl.create_default_context()
USER_AGENT = 'Mozilla/5.0 (TextbookSharingBot/1.0)'

CATEGORY_HINTS = {
    '高等数学': ['高等数学', '微积分'],
    '线性代数': ['线性代数'],
    '概率论': ['概率论', '数理统计'],
    '英语': ['大学英语', '英语'],
    '计算机': ['计算机', '程序设计', '数据结构', '算法'],
    '物理': ['大学物理', '物理学'],
    '化学': ['化学', '有机化学', '无机化学'],
    '经济': ['经济学', '宏观经济学', '微观经济学'],
    '管理': ['管理学', '市场营销'],
    '法学': ['法学', '法律'],
}


def fetch_json(url: str, timeout: int = 12):
    request = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode('utf-8', errors='ignore'))


def fetch_bytes(url: str, timeout: int = 15):
    request = Request(url, headers={'User-Agent': USER_AGENT})
    with urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
        return response.read()


def normalize_isbn(value: str) -> str:
    if not value:
        return ''
    normalized = ''.join(character for character in value if character.isdigit() or character.upper() == 'X')
    if len(normalized) in (10, 13):
        return normalized
    return ''


def get_category_chain_names(textbook: Textbook):
    names = []
    category = textbook.category
    while category is not None:
        if category.name:
            names.append(category.name)
        category = category.parent
    return names


def normalize_title_candidates(title: str):
    raw = (title or '').strip()
    if not raw:
        return []

    candidates = [raw]
    simplified = re.sub(r'\s+', ' ', raw)
    simplified = re.sub(r'学习指南\s*\d+$', '', simplified).strip()
    simplified = re.sub(r'第\d+版', '', simplified).strip()
    simplified = re.sub(r'\(.*?\)|（.*?）', '', simplified).strip()
    simplified = re.sub(r'\d+$', '', simplified).strip()
    if simplified and simplified not in candidates:
        candidates.append(simplified)

    main_keyword = re.split(r'[：:·\-—\s]', simplified)[0].strip() if simplified else ''
    if main_keyword and len(main_keyword) >= 2 and main_keyword not in candidates:
        candidates.append(main_keyword)

    return [item for item in candidates if item]


def build_query_candidates(textbook: Textbook):
    title_candidates = normalize_title_candidates(textbook.title)
    category_names = get_category_chain_names(textbook)

    category_keywords = []
    for name in category_names:
        for key, values in CATEGORY_HINTS.items():
            if key in name:
                for value in values:
                    if value not in category_keywords:
                        category_keywords.append(value)
        if name not in category_keywords:
            category_keywords.append(name)

    queries = []
    for base in title_candidates:
        if base not in queries:
            queries.append(base)
        for keyword in category_keywords:
            combined = f'{base} {keyword}'.strip()
            if combined not in queries:
                queries.append(combined)

    return queries[:10]


def search_open_library(title: str):
    query = urlencode({'title': title, 'limit': 5})
    url = f'https://openlibrary.org/search.json?{query}'
    payload = fetch_json(url)
    docs = payload.get('docs') or []
    if not docs:
        return None

    first = docs[0]
    cover_id = first.get('cover_i')
    cover_url = f'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg' if cover_id else ''

    isbn_list = first.get('isbn') or []
    isbn = ''
    for isbn_value in isbn_list:
        isbn = normalize_isbn(isbn_value)
        if isbn:
            break

    publisher_list = first.get('publisher') or []
    author_list = first.get('author_name') or []

    return {
        'title': first.get('title') or title,
        'author': (author_list[0] if author_list else ''),
        'publisher': (publisher_list[0] if publisher_list else ''),
        'isbn': isbn,
        'edition': '',
        'description': '',
        'cover_url': cover_url,
        'source': 'openlibrary'
    }


def search_google_books(title: str):
    query = quote(f'intitle:{title}')
    url = f'https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=5&langRestrict=zh'
    payload = fetch_json(url)
    items = payload.get('items') or []
    if not items:
        return None

    volume = items[0].get('volumeInfo') or {}
    identifiers = volume.get('industryIdentifiers') or []
    isbn = ''
    for identifier in identifiers:
        isbn = normalize_isbn(identifier.get('identifier', ''))
        if isbn:
            break

    image_links = volume.get('imageLinks') or {}
    cover_url = image_links.get('thumbnail') or image_links.get('smallThumbnail') or ''
    if cover_url.startswith('http://'):
        cover_url = 'https://' + cover_url[len('http://'):]

    authors = volume.get('authors') or []
    publisher = volume.get('publisher') or ''
    description = volume.get('description') or ''

    return {
        'title': volume.get('title') or title,
        'author': (authors[0] if authors else ''),
        'publisher': publisher,
        'isbn': isbn,
        'edition': '',
        'description': description[:500],
        'cover_url': cover_url,
        'source': 'google_books'
    }


def enrich_single_textbook(textbook: Textbook):
    open_data = None
    query_candidates = build_query_candidates(textbook)

    for query in query_candidates:
        try:
            open_data = search_open_library(query)
        except Exception:
            open_data = None
        if open_data:
            break

    if not open_data:
        for query in query_candidates:
            try:
                open_data = search_google_books(query)
            except Exception:
                open_data = None
            if open_data:
                break

    if not open_data:
        return False, 'not_found'

    changed = False

    if open_data.get('author') and textbook.author != open_data['author']:
        textbook.author = open_data['author']
        changed = True

    if open_data.get('publisher') and (not textbook.publisher or textbook.publisher == ''):
        textbook.publisher = open_data['publisher']
        changed = True

    if open_data.get('isbn') and (not textbook.isbn or len(textbook.isbn) < 10):
        textbook.isbn = open_data['isbn']
        changed = True

    description = open_data.get('description')
    if description:
        textbook.description = f"[OPEN_DATA:{open_data.get('source')}] {description}"
        changed = True

    cover_url = open_data.get('cover_url') or ''
    if cover_url:
        try:
            image_content = fetch_bytes(cover_url)
            if image_content:
                file_name = f'open_{textbook.id}.jpg'
                textbook.cover_image.save(file_name, ContentFile(image_content), save=False)
                changed = True
        except Exception:
            pass

    if changed:
        textbook.save()
        return True, open_data.get('source')

    return False, 'no_change'


class Command(BaseCommand):
    help = '从公开图书API回填教材信息与封面图（Open Library / Google Books）'

    def add_arguments(self, parser):
        parser.add_argument('--only-seeded', action='store_true', help='仅处理自动生成数据（description 以 [AUTO_SEED] 开头）')
        parser.add_argument('--max-items', type=int, default=0, help='最多处理多少条，0 为全部')

    def handle(self, *args, **options):
        only_seeded = bool(options['only_seeded'])
        max_items = int(options['max_items'])

        queryset = Textbook.objects.all().order_by('id')
        if only_seeded:
            queryset = queryset.filter(description__startswith='[AUTO_SEED]')

        if max_items > 0:
            queryset = queryset[:max_items]

        total = queryset.count() if hasattr(queryset, 'count') else len(queryset)
        self.stdout.write(f'准备处理 {total} 本教材...')

        success_count = 0
        not_found_count = 0
        no_change_count = 0

        for textbook in queryset:
            ok, source = enrich_single_textbook(textbook)
            if ok:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f'[{textbook.id}] 已更新（来源: {source}） {textbook.title}'))
            else:
                if source == 'not_found':
                    not_found_count += 1
                else:
                    no_change_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'完成：成功 {success_count}，未命中 {not_found_count}，无变化 {no_change_count}。'
        ))
