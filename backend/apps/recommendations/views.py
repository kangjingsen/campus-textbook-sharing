from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.textbooks.models import Textbook
from apps.textbooks.serializers import TextbookListSerializer
from .models import BrowsingHistory, RecommendationCache, WishlistItem
from .serializers import BrowsingHistorySerializer, RecommendationSerializer, WishlistItemSerializer
from .tasks import update_user_recommendations


class RecommendationListView(APIView):
    """获取个性化推荐列表"""

    def get(self, request):
        user = request.user
        top_k = int(request.query_params.get('limit', 10))
        refresh = str(request.query_params.get('refresh', '')).lower() in ('1', 'true', 'yes')

        # 先尝试从缓存获取（可通过 refresh 强制实时重算）
        cached = RecommendationCache.objects.filter(user=user)[:top_k]

        if cached.exists() and not refresh:
            serializer = RecommendationSerializer(cached, many=True)
            return Response({'recommendations': serializer.data, 'source': 'cache'})

        # 无缓存或强制刷新时实时计算
        update_user_recommendations(user.id, top_k=top_k)
        cached = RecommendationCache.objects.filter(user=user)[:top_k]

        if cached.exists():
            serializer = RecommendationSerializer(cached, many=True)
            return Response({'recommendations': serializer.data, 'source': 'realtime'})

        # 冷启动：返回热门教材
        popular = Textbook.objects.filter(status='approved').exclude(owner=user).order_by('-view_count')[:top_k]
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


class WishlistListCreateView(generics.ListCreateAPIView):
    """我的心愿单"""
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        qs = WishlistItem.objects.filter(user=self.request.user)
        status_val = self.request.query_params.get('status')
        if status_val:
            qs = qs.filter(status=status_val)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """心愿单项详情"""
    serializer_class = WishlistItemSerializer

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user)
