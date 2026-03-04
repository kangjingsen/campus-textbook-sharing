"""
基于用户的协同过滤推荐算法
构建用户-教材交互矩阵，计算用户相似度，推荐相似用户喜欢的教材
"""
import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial.distance import cosine
from collections import defaultdict
from django.db.models import Count

from apps.users.models import User
from apps.textbooks.models import Textbook
from apps.orders.models import Order
from .models import BrowsingHistory


def build_interaction_matrix():
    """
    构建用户-教材交互矩阵
    评分规则：浏览=1分, 下单=3分, 完成交易=5分
    """
    users = list(User.objects.filter(is_active=True).values_list('id', flat=True))
    textbooks = list(Textbook.objects.filter(status__in=['approved', 'sold', 'rented', 'completed'])
                     .values_list('id', flat=True))

    if not users or not textbooks:
        return None, [], []

    user_idx = {uid: i for i, uid in enumerate(users)}
    textbook_idx = {tid: i for i, tid in enumerate(textbooks)}

    n_users = len(users)
    n_textbooks = len(textbooks)
    matrix = np.zeros((n_users, n_textbooks), dtype=np.float32)

    # 浏览记录 -> 1分
    for record in BrowsingHistory.objects.filter(
        user_id__in=users, textbook_id__in=textbooks
    ).values('user_id', 'textbook_id', 'view_count'):
        u = user_idx.get(record['user_id'])
        t = textbook_idx.get(record['textbook_id'])
        if u is not None and t is not None:
            matrix[u][t] = max(matrix[u][t], min(record['view_count'], 2))  # 浏览 cap at 2

    # 下单 -> 3分
    for order in Order.objects.filter(
        buyer_id__in=users, textbook_id__in=textbooks,
        status__in=['pending', 'confirmed']
    ).values('buyer_id', 'textbook_id'):
        u = user_idx.get(order['buyer_id'])
        t = textbook_idx.get(order['textbook_id'])
        if u is not None and t is not None:
            matrix[u][t] = max(matrix[u][t], 3)

    # 完成交易 -> 5分
    for order in Order.objects.filter(
        buyer_id__in=users, textbook_id__in=textbooks,
        status='completed'
    ).values('buyer_id', 'textbook_id'):
        u = user_idx.get(order['buyer_id'])
        t = textbook_idx.get(order['textbook_id'])
        if u is not None and t is not None:
            matrix[u][t] = 5

    return matrix, users, textbooks


def compute_user_similarity(matrix):
    """计算用户相似度矩阵（余弦相似度）"""
    n_users = matrix.shape[0]
    similarity = np.zeros((n_users, n_users), dtype=np.float32)

    for i in range(n_users):
        for j in range(i + 1, n_users):
            if np.any(matrix[i]) and np.any(matrix[j]):
                sim = 1 - cosine(matrix[i], matrix[j])
                if not np.isnan(sim):
                    similarity[i][j] = sim
                    similarity[j][i] = sim

    return similarity


def get_collaborative_recommendations(user_id, top_k=10, n_similar_users=20):
    """
    基于协同过滤获取推荐列表
    1. 构建交互矩阵
    2. 计算用户相似度
    3. 取 Top-K 相似用户的高分教材
    """
    result = build_interaction_matrix()
    if result is None:
        return []

    matrix, users, textbooks = result

    if user_id not in [u for u in users]:
        return []

    user_idx_map = {uid: i for i, uid in enumerate(users)}
    u_idx = user_idx_map.get(user_id)
    if u_idx is None:
        return []

    similarity = compute_user_similarity(matrix)

    # 找到最相似的用户
    sim_scores = similarity[u_idx]
    similar_user_indices = np.argsort(sim_scores)[::-1][:n_similar_users]

    # 推荐候选：相似用户交互过而当前用户没交互过的教材
    user_interacted = set(np.where(matrix[u_idx] > 0)[0])
    candidates = defaultdict(float)

    for sim_u_idx in similar_user_indices:
        if sim_scores[sim_u_idx] <= 0:
            continue
        for t_idx in range(len(textbooks)):
            if t_idx not in user_interacted and matrix[sim_u_idx][t_idx] > 0:
                candidates[t_idx] += sim_scores[sim_u_idx] * matrix[sim_u_idx][t_idx]

    # 按得分排序取 Top-K
    sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)[:top_k]

    recommendations = []
    for t_idx, score in sorted_candidates:
        textbook_id = textbooks[t_idx]
        recommendations.append({
            'textbook_id': textbook_id,
            'score': float(score),
            'reason': '协同过滤推荐'
        })

    return recommendations
