from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.textbooks.models import Textbook
from apps.textbooks.serializers import TextbookListSerializer
from .models import BrowsingHistory, RecommendationCache
from .serializers import BrowsingHistorySerializer, RecommendationSerializer
from .tasks import update_user_recommendations


class RecommendationListView(APIView):
    """获取个性化推荐列表"""

    def get(self, request):
        user = request.user
        top_k = int(request.query_params.get('limit', 10))

        # 先尝试从缓存获取
        cached = RecommendationCache.objects.filter(user=user)[:top_k]

        if cached.exists():
            serializer = RecommendationSerializer(cached, many=True)
            return Response({'recommendations': serializer.data, 'source': 'cache'})

        # 无缓存时实时计算
        update_user_recommendations(user.id, top_k=top_k)
        cached = RecommendationCache.objects.filter(user=user)[:top_k]

        if cached.exists():
            serializer = RecommendationSerializer(cached, many=True)
            return Response({'recommendations': serializer.data, 'source': 'realtime'})

        # 冷启动：返回热门教材
        popular = Textbook.objects.filter(status='approved').order_by('-view_count')[:top_k]
        serializer = TextbookListSerializer(popular, many=True)
        return Response({'recommendations': serializer.data, 'source': 'popular'})


class PopularTextbooksView(generics.ListAPIView):
    """热门教材排行"""
    serializer_class = TextbookListSerializer

    def get_queryset(self):
        return Textbook.objects.filter(status='approved').order_by('-view_count')[:20]


class BrowsingHistoryListView(generics.ListAPIView):
    """用户浏览历史"""
    serializer_class = BrowsingHistorySerializer

    def get_queryset(self):
        return BrowsingHistory.objects.filter(user=self.request.user).order_by('-last_viewed_at')
