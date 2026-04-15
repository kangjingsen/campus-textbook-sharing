import hashlib
import io
import re
from pathlib import Path
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image, ImageDraw, ImageFont


USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
)


def _normalize_text(value: str) -> str:
    text = (value or '').strip().lower()
    return re.sub(r'[^0-9a-z\u4e00-\u9fff]+', '', text)


def _normalize_isbn(value: str) -> str:
    return re.sub(r'[^0-9xX]', '', value or '').upper()


def _cover_dir() -> Path:
    return Path(settings.MEDIA_ROOT) / 'covers'


def _list_existing_cover_files() -> list:
    cdir = _cover_dir()
    if not cdir.exists():
        return []
    files = []
    for path in cdir.rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp'}:
            files.append(path)
    return files


def _find_local_cover_by_isbn(textbook):
    isbn = _normalize_isbn(textbook.isbn)
    if not isbn:
        return None
    for path in _list_existing_cover_files():
        if isbn in _normalize_isbn(path.stem):
            return path
    return None


def _find_local_cover_by_title(textbook):
    title = _normalize_text(textbook.title)
    if not title:
        return None
    for path in _list_existing_cover_files():
        stem = _normalize_text(path.stem)
        if not stem:
            continue
        if title in stem or stem in title:
            return path
    return None


def _download_cover_by_isbn(textbook) -> bytes:
    isbn = _normalize_isbn(textbook.isbn)
    if not isbn:
        return b''

    url = f'https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg?default=false'
    req = Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urlopen(req, timeout=10) as resp:
            content_type = (resp.headers.get('Content-Type') or '').lower()
            if 'image' not in content_type:
                return b''
            data = resp.read()
            if len(data) < 1024:
                return b''
            return data
    except BaseException:
        return b''


def _pick_font(size: int):
    candidates = [
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simsun.ttc',
    ]
    for font_path in candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except BaseException:
            continue
    return ImageFont.load_default()


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int) -> list:
    if not text:
        return []

    chars = list(text)
    lines = []
    current = ''
    for ch in chars:
        candidate = current + ch
        bbox = draw.textbbox((0, 0), candidate, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ch
        else:
            lines.append(ch)
            current = ''
        if len(lines) >= max_lines:
            break

    if len(lines) < max_lines and current:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    if len(lines) == max_lines and (len(''.join(lines)) < len(text)):
        lines[-1] = (lines[-1][:-1] + '…') if len(lines[-1]) > 1 else lines[-1]
    return lines


def _generate_cover_image(textbook) -> bytes:
    width, height = 600, 840
    digest = hashlib.md5(f'{textbook.title}|{textbook.author}|{textbook.publisher}'.encode('utf-8')).digest()
    bg1 = (40 + digest[0] % 80, 70 + digest[1] % 100, 100 + digest[2] % 100)
    bg2 = (20 + digest[3] % 60, 30 + digest[4] % 80, 50 + digest[5] % 90)

    img = Image.new('RGB', (width, height), bg1)
    draw = ImageDraw.Draw(img)

    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(bg1[0] * (1 - t) + bg2[0] * t),
            int(bg1[1] * (1 - t) + bg2[1] * t),
            int(bg1[2] * (1 - t) + bg2[2] * t),
        )
        draw.line((0, y, width, y), fill=color)

    panel_margin = 36
    draw.rounded_rectangle(
        (panel_margin, panel_margin, width - panel_margin, height - panel_margin),
        radius=28,
        fill=(255, 255, 255, 228),
        outline=(245, 245, 245),
        width=2,
    )

    title_font = _pick_font(46)
    meta_font = _pick_font(28)
    tag_font = _pick_font(22)

    text_x = panel_margin + 36
    text_w = width - panel_margin * 2 - 72
    current_y = panel_margin + 60

    lines = _wrap_lines(draw, textbook.title or '未命名教材', title_font, text_w, max_lines=4)
    for line in lines:
        draw.text((text_x, current_y), line, font=title_font, fill=(38, 47, 64))
        line_h = draw.textbbox((0, 0), line, font=title_font)[3]
        current_y += line_h + 12

    current_y += 12
    author_line = f'作者：{textbook.author or "未知"}'
    publisher_line = f'出版社：{textbook.publisher or "未提供"}'
    draw.text((text_x, current_y), author_line, font=meta_font, fill=(73, 89, 112))
    current_y += 46
    draw.text((text_x, current_y), publisher_line, font=meta_font, fill=(73, 89, 112))

    footer_h = 84
    draw.rounded_rectangle(
        (panel_margin + 24, height - panel_margin - footer_h - 18, width - panel_margin - 24, height - panel_margin - 18),
        radius=18,
        fill=(36, 64, 108),
    )
    draw.text(
        (panel_margin + 46, height - panel_margin - footer_h + 6),
        '教材共享平台 · 自动生成封面',
        font=tag_font,
        fill=(255, 255, 255),
    )

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=92)
    return buffer.getvalue()


def _save_cover_bytes(textbook, image_bytes: bytes, source: str) -> bool:
    if not image_bytes:
        return False
    file_name = f'{source}_{textbook.id}.jpg'
    textbook.cover_image.save(file_name, ContentFile(image_bytes), save=True)
    return True


def _save_cover_from_path(textbook, path: Path, source: str) -> bool:
    if not path or not path.exists():
        return False
    try:
        with open(path, 'rb') as f:
            data = f.read()
        return _save_cover_bytes(textbook, data, source)
    except BaseException:
        return False


def ensure_textbook_cover(textbook, try_online: bool = True) -> str:
    if getattr(textbook, 'cover_image', None):
        return 'exists'

    local_by_isbn = _find_local_cover_by_isbn(textbook)
    if _save_cover_from_path(textbook, local_by_isbn, 'matched_isbn'):
        return 'matched_isbn'

    local_by_title = _find_local_cover_by_title(textbook)
    if _save_cover_from_path(textbook, local_by_title, 'matched_title'):
        return 'matched_title'

    if try_online:
        online_cover = _download_cover_by_isbn(textbook)
        if _save_cover_bytes(textbook, online_cover, 'online_isbn'):
            return 'online_isbn'

    generated = _generate_cover_image(textbook)
    if _save_cover_bytes(textbook, generated, 'generated'):
        return 'generated'

    return 'failed'