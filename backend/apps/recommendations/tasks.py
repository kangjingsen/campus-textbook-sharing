from celery import shared_task
from django.db.models import Count
from apps.users.models import User
from apps.textbooks.models import Textbook
from .models import RecommendationCache
from .collaborative_filtering import get_collaborative_recommendations
from .content_based import get_content_recommendations, compute_user_preferences


@shared_task
def update_recommendations():
    """
    定时任务：更新所有活跃用户的推荐缓存
    混合策略：协同过滤 60% + 内容推荐 40%
    """
    active_users = User.objects.filter(is_active=True, role='student')

    for user in active_users:
        try:
            update_user_recommendations(user.id)
        except Exception as e:
            print(f'更新用户 {user.username} 推荐失败: {e}')

    return f'已更新 {active_users.count()} 个用户的推荐'


def update_user_recommendations(user_id, top_k=20):
    """更新单个用户的推荐"""
    allowed_ids = set(
        Textbook.objects.filter(status='approved').exclude(owner_id=user_id).values_list('id', flat=True)
    )

    cf_recs = get_collaborative_recommendations(user_id, top_k=top_k)
    cb_recs = get_content_recommendations(user_id, top_k=top_k)

    # 混合推荐：协同过滤 60% + 内容推荐 40%
    merged = {}

    for rec in cf_recs:
        tid = rec['textbook_id']
        if tid not in allowed_ids:
            continue
        merged[tid] = {
            'score': rec['score'] * 0.6,
            'reason': rec['reason']
        }

    for rec in cb_recs:
        tid = rec['textbook_id']
        if tid not in allowed_ids:
            continue
        if tid in merged:
            merged[tid]['score'] += rec['score'] * 0.4
            merged[tid]['reason'] = '综合推荐'
        else:
            merged[tid] = {
                'score': rec['score'] * 0.4,
                'reason': rec['reason']
            }

    # 清除旧缓存
    RecommendationCache.objects.filter(user_id=user_id).delete()

    # 保存新推荐
    sorted_recs = sorted(merged.items(), key=lambda x: x[1]['score'], reverse=True)[:top_k]
    for textbook_id, data in sorted_recs:
        try:
            RecommendationCache.objects.create(
                user_id=user_id,
                textbook_id=textbook_id,
                score=data['score'],
                reason=data['reason']
            )
        except Exception:
            pass  # 教材可能已被删除

    return len(sorted_recs)
