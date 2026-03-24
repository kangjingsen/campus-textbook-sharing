import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.textbooks.models import Category, Textbook


@dataclass
class Rule:
    target: str
    keywords: List[str]


RULES: List[Rule] = [
    Rule('数据结构', ['data structures', 'data structure', '数据结构']),
    Rule('操作系统', ['operating systems', 'operating system', 'os ', '操作系统']),
    Rule('计算机网络', ['computer network', 'computer networks', 'networking', '计算机网络', '网络协议']),
    Rule('数据库', ['database systems', 'database system', 'relational database', 'sql', '数据库']),
    Rule('编程语言', ['programming', 'java', 'python', 'c++', 'c language', '编程语言', '程序设计']),
    Rule('人工智能', ['artificial intelligence', 'machine learning', 'deep learning', 'neural network', 'ai ', '人工智能']),
    Rule('高等数学', ['calculus', 'pre-calculus', 'advanced mathematics', '高等数学', '微积分']),
    Rule('线性代数', ['linear algebra', 'matrix', '线性代数']),
    Rule('概率统计', ['probability', 'statistics', 'stochastic', '概率', '统计']),
    Rule('经济学', ['economics', 'microeconomics', 'macroeconomics', 'political economy', '经济学', '宏观经济', '微观经济']),
    Rule('管理学', ['management', 'managerial', 'business administration', '管理学']),
    Rule('会计学', ['accounting', 'audit', '会计学', '财务会计', '成本会计']),
    Rule('金融学', ['finance', 'financial', 'investment', 'banking', '金融学']),
    Rule('英语', ['english', 'toefl', 'ielts', '大学英语', '英语']),
    Rule('中文', ['chinese literature', 'chinese language', '中国文学', '现代汉语', '古代汉语', '中文']),
    Rule('法学', ['law', 'jurisprudence', 'legal', '法学', '法律']),
    Rule('历史', ['history', 'historical', '历史']),
    Rule('哲学', ['philosophy', 'ethics', 'logic', '哲学']),
    Rule('物理', ['physics', 'electromagnetism', 'mechanics', 'thermodynamics', '量子', '大学物理', '物理']),
    Rule('化学', ['chemistry', 'organic chemistry', 'inorganic chemistry', 'physical chemistry', '化学']),
    Rule('机械工程', ['mechanical engineering', 'mechanics design', 'cad', '机械工程', '机械设计']),
    Rule('电子信息', ['electronic', 'electronics', 'signal and system', 'communication principles', '电子信息', '通信原理']),
    Rule('计算机科学', ['computer science', '计算机科学']),
    Rule('数学', ['mathematics', 'mathematical', 'math', '数学']),
]


def normalize_text(value: str) -> str:
    value = (value or '').lower()
    value = value.replace('（', '(').replace('）', ')')
    value = re.sub(r'[_\-:,.;!?/\\\(\)\[\]{}]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return f' {value} '


def contains_keyword(text: str, keyword: str) -> bool:
    keyword = (keyword or '').strip().lower()
    if not keyword:
        return False

    # 中文词直接包含匹配；英文词按单词边界匹配，避免误击。
    if re.search(r'[\u4e00-\u9fff]', keyword):
        return keyword in text

    if re.search(r'[a-zA-Z]', keyword):
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return re.search(pattern, text, flags=re.IGNORECASE) is not None

    return keyword in text


def get_scope_filter(scope: str):
    if scope == 'real-web':
        return {'description__startswith': '[REAL_WEB_'}
    if scope == 'auto-seed':
        return {'description__startswith': '[AUTO_SEED]'}
    return {}


def build_category_lookup() -> Dict[str, Category]:
    by_name: Dict[str, List[Category]] = defaultdict(list)
    for category in Category.objects.filter(is_active=True):
        by_name[category.name].append(category)

    resolved = {}
    for name, items in by_name.items():
        # 同名时优先最细分类（level 最大）
        items = sorted(items, key=lambda item: (item.level, item.id), reverse=True)
        resolved[name] = items[0]
    return resolved


def predict_category(textbook: Textbook, category_lookup: Dict[str, Category], min_score: int) -> Tuple[Optional[Category], int, List[str]]:
    title_text = normalize_text(textbook.title or '')
    author_text = normalize_text(textbook.author or '')
    publisher_text = normalize_text(textbook.publisher or '')

    scores = Counter()
    reasons = defaultdict(list)

    for rule in RULES:
        if rule.target not in category_lookup:
            continue
        for keyword in rule.keywords:
            hit_title = contains_keyword(title_text, keyword)
            hit_author = contains_keyword(author_text, keyword)
            hit_publisher = contains_keyword(publisher_text, keyword)
            if hit_title or hit_author or hit_publisher:
                # 标题权重最高，作者/出版社仅做弱信号。
                base = 1 + min(3, max(0, (len(keyword) - 4) // 6))
                weight = 0
                if hit_title:
                    weight += base * 3
                if hit_author:
                    weight += base
                if hit_publisher:
                    weight += base
                scores[rule.target] += weight
                reasons[rule.target].append(keyword)

    if not scores:
        return None, 0, []

    target_name, best_score = scores.most_common(1)[0]
    if best_score < min_score:
        return None, best_score, []

    matched_keywords = sorted(set(reasons[target_name]))
    return category_lookup[target_name], best_score, matched_keywords


class Command(BaseCommand):
    help = '按书名/作者/出版社关键词批量重分类教材（默认处理 REAL_WEB 扩展数据）。'

    def add_arguments(self, parser):
        parser.add_argument('--scope', type=str, default='real-web', choices=['real-web', 'auto-seed', 'all'], help='重分类范围')
        parser.add_argument('--limit', type=int, default=0, help='最多处理条数，0 为全部')
        parser.add_argument('--min-score', type=int, default=2, help='命中最小分数，默认 2')
        parser.add_argument('--dry-run', action='store_true', help='仅预览，不落库')

    @transaction.atomic
    def handle(self, *args, **options):
        scope = options['scope']
        limit = max(0, int(options['limit']))
        min_score = max(1, int(options['min_score']))
        dry_run = bool(options['dry_run'])

        category_lookup = build_category_lookup()
        if not category_lookup:
            self.stdout.write(self.style.ERROR('未找到可用分类，无法重分类。'))
            return

        queryset = Textbook.objects.select_related('category').filter(**get_scope_filter(scope)).order_by('id')
        total = queryset.count()
        if limit > 0:
            queryset = queryset[:limit]

        self.stdout.write(f'范围: {scope}，候选教材: {total}，min_score: {min_score}，dry_run: {dry_run}')

        changed = 0
        unchanged = 0
        no_match = 0
        hit_counter = Counter()

        preview_rows = []
        for textbook in queryset:
            target, score, keywords = predict_category(textbook, category_lookup, min_score=min_score)
            if target is None:
                no_match += 1
                continue

            current_id = textbook.category_id
            current_name = textbook.category.name if textbook.category else '未分类'
            if current_id == target.id:
                unchanged += 1
                continue

            hit_counter[target.name] += 1
            changed += 1
            preview_rows.append((
                textbook.id,
                (textbook.title or '')[:42],
                current_name,
                target.name,
                score,
                ', '.join(keywords[:3])
            ))

            if not dry_run:
                textbook.category = target
                textbook.save(update_fields=['category'])

        self.stdout.write(self.style.SUCCESS(f'预测可改: {changed}，已是目标分类: {unchanged}，未命中: {no_match}'))

        if hit_counter:
            self.stdout.write('分类落点统计（Top 15）:')
            for name, count in hit_counter.most_common(15):
                self.stdout.write(f'  - {name}: {count}')

        if preview_rows:
            self.stdout.write('变更预览（前 20 条）:')
            for row in preview_rows[:20]:
                self.stdout.write(f'  - #{row[0]} {row[1]} | {row[2]} -> {row[3]} | score={row[4]} | {row[5]}')

        if dry_run:
            self.stdout.write(self.style.WARNING('dry-run 模式未写入数据库。'))
        else:
            self.stdout.write(self.style.SUCCESS('重分类已写入数据库。'))
