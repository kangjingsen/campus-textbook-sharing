"""
基于内容的推荐算法
根据用户历史交互的教材分类、作者偏好，推荐同类教材
"""
from collections import defaultdict
from django.db.models import Count, Q

from apps.textbooks.models import Textbook
from apps.orders.models import Order
from .models import BrowsingHistory, UserPreference


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

    # 获取用户已交互过的教材ID
    interacted_ids = set()
    interacted_ids.update(
        BrowsingHistory.objects.filter(user_id=user_id).values_list('textbook_id', flat=True)
    )
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
