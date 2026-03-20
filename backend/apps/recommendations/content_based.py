"""
基于内容的推荐算法
根据用户历史交互的教材分类、作者偏好，推荐同类教材
"""
from collections import defaultdict
import re
from django.db.models import Count, Q

from apps.textbooks.models import Textbook
from apps.orders.models import Order
from .models import BrowsingHistory, UserPreference, WishlistItem


def _normalize_keyword(text):
    """规范化心愿关键词，提升书名匹配鲁棒性。"""
    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', (text or '')).lower()


def _build_wish_title_query(keyword):
    """构造心愿关键词匹配查询：标题优先，同时覆盖作者/ISBN/出版社/描述。"""
    clean = _normalize_keyword(keyword)
    if not clean:
        return Q()

    query = (
        Q(title__icontains=keyword)
        | Q(title__icontains=clean)
        | Q(author__icontains=keyword)
        | Q(isbn__icontains=keyword)
        | Q(publisher__icontains=keyword)
        | Q(description__icontains=keyword)
    )

    # 对长标题补充分段匹配，避免“整句不完全一致”导致命中失败
    if len(clean) >= 6:
        fragments = set()
        step = 3
        size = 4
        for i in range(0, max(len(clean) - size + 1, 1), step):
            frag = clean[i:i + size]
            if len(frag) >= 3:
                fragments.add(frag)
        for frag in list(fragments)[:8]:
                query |= Q(title__icontains=frag) | Q(description__icontains=frag)

    return query


def compute_user_preferences(user_id):
    """计算用户偏好分数"""
    preference_scores = defaultdict(float)

    # 浏览历史中的分类偏好
    browsed = BrowsingHistory.objects.filter(
        user_id=user_id,
        textbook__category__isnull=False
    ).values('textbook__category_id').annotate(
        count=Count('id')
    )
    for item in browsed:
        preference_scores[item['textbook__category_id']] += item['count'] * 1.0

    # 下单/交易的分类偏好
    ordered = Order.objects.filter(
        buyer_id=user_id,
        textbook__category__isnull=False,
        status__in=['pending', 'confirmed', 'completed']
    ).values('textbook__category_id').annotate(
        count=Count('id')
    )
    for item in ordered:
        preference_scores[item['textbook__category_id']] += item['count'] * 3.0

    # 完成交易的分类偏好权重更高
    completed = Order.objects.filter(
        buyer_id=user_id,
        textbook__category__isnull=False,
        status='completed'
    ).values('textbook__category_id').annotate(
        count=Count('id')
    )
    for item in completed:
        preference_scores[item['textbook__category_id']] += item['count'] * 2.0  # 额外加分

    # 心愿单分类偏好
    wished = WishlistItem.objects.filter(
        user_id=user_id,
        status='open',
        category__isnull=False
    ).values('category_id', 'priority')
    for item in wished:
        preference_scores[item['category_id']] += max(item['priority'], 1) * 4.0

    # 保存偏好分数
    for category_id, score in preference_scores.items():
        UserPreference.objects.update_or_create(
            user_id=user_id,
            category_id=category_id,
            defaults={'score': score}
        )

    return preference_scores


def get_content_recommendations(user_id, top_k=10):
    """基于内容的推荐"""
    # 计算/获取用户偏好
    preferences = compute_user_preferences(user_id)

    if not preferences:
        return []

    # 获取用户已成交/下单过的教材ID（仅排除已交易，保留“浏览过但仍可能感兴趣”的教材）
    interacted_ids = set()
    interacted_ids.update(
        Order.objects.filter(buyer_id=user_id).values_list('textbook_id', flat=True)
    )

    # 获取用户偏好作者
    favorite_authors = list(
        BrowsingHistory.objects.filter(user_id=user_id)
        .values_list('textbook__author', flat=True)
        .distinct()[:5]
    )

    # 按偏好分类推荐
    sorted_categories = sorted(preferences.items(), key=lambda x: x[1], reverse=True)
    recommendations = []

    for category_id, pref_score in sorted_categories[:5]:
        candidates = Textbook.objects.filter(
            category_id=category_id,
            status='approved'
        ).exclude(
            id__in=interacted_ids
        ).exclude(
            owner_id=user_id
        ).order_by('-view_count')[:top_k]

        for tb in candidates:
            score = pref_score
            if tb.author in favorite_authors:
                score *= 1.5  # 作者加权
            recommendations.append({
                'textbook_id': tb.id,
                'score': score,
                'reason': f'基于您对「{tb.category.name}」的兴趣'
            })

    # 心愿单关键词补充推荐（支持无分类心愿）
    wish_items = WishlistItem.objects.filter(user_id=user_id, status='open').order_by('-priority')[:10]
    for wish in wish_items:
        keyword = (wish.title or '').strip()
        author_kw = (wish.author or '').strip()
        isbn_kw = (wish.isbn or '').strip()
        if not keyword and not author_kw and not isbn_kw:
            continue

        title_query = _build_wish_title_query(keyword) if keyword else Q()
        if author_kw:
            title_query |= Q(author__icontains=author_kw)
        if isbn_kw:
            title_query |= Q(isbn__icontains=isbn_kw)
        if not title_query:
            continue

        keyword_candidates = Textbook.objects.filter(
            title_query,
            status='approved'
        ).exclude(
            id__in=interacted_ids
        ).exclude(
            owner_id=user_id
        ).order_by('-view_count', '-created_at')[:max(top_k * 5, 30)]

        clean_keyword = _normalize_keyword(keyword)
        clean_author = _normalize_keyword(author_kw)
        clean_isbn = _normalize_keyword(isbn_kw)
        for tb in keyword_candidates:
            score = 5.0 * max(wish.priority, 1)
            tb_title = _normalize_keyword(tb.title)
            tb_author = _normalize_keyword(tb.author)
            tb_isbn = _normalize_keyword(tb.isbn)

            # 强匹配加权：优先保障与心愿高度相关的教材进入前列
            if clean_keyword and tb_title == clean_keyword:
                score += 25
            elif clean_keyword and clean_keyword in tb_title:
                score += 12
            elif clean_keyword and (clean_keyword in _normalize_keyword(tb.description or '')):
                score += 6

            if clean_author and clean_author in tb_author:
                score += 8
            if clean_isbn and clean_isbn == tb_isbn:
                score += 20

            recommendations.append({
                'textbook_id': tb.id,
                'score': score,
                'reason': f'匹配您的心愿单「{wish.title}」'
            })

    # 去重并排序
    seen = set()
    unique_recs = []
    for rec in sorted(recommendations, key=lambda x: x['score'], reverse=True):
        if rec['textbook_id'] not in seen:
            seen.add(rec['textbook_id'])
            unique_recs.append(rec)
        if len(unique_recs) >= top_k:
            break

    return unique_recs
