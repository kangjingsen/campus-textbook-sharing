from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

from apps.textbooks.models import Textbook
from apps.textbooks.serializers import TextbookListSerializer
from .models import ReviewRecord, SensitiveWord
from .serializers import ReviewRecordSerializer, ReviewActionSerializer, SensitiveWordSerializer
from .sensitive_filter import reload_sensitive_filter
from utils.permissions import IsAdmin


class PendingReviewListView(generics.ListAPIView):
    """待审核教材列表"""
    serializer_class = TextbookListSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        return Textbook.objects.filter(status='pending_review').order_by('created_at')


class ReviewActionView(APIView):
    """审核操作：通过/驳回"""
    permission_classes = [IsAdmin]

    def post(self, request, pk):
        try:
            textbook = Textbook.objects.get(pk=pk)
        except Textbook.DoesNotExist:
            return Response({'error': '教材不存在'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review_status = serializer.validated_data['status']
        reason = serializer.validated_data.get('reason', '')

        # 创建审核记录
        ReviewRecord.objects.create(
            textbook=textbook,
            reviewer=request.user,
            status=review_status,
            reason=reason,
            is_auto=False
        )

        # 更新教材状态
        textbook.status = review_status
        textbook.save(update_fields=['status'])

        status_text = '通过' if review_status == 'approved' else '驳回'
        return Response({'message': f'审核{status_text}成功'})


class ReviewRecordListView(generics.ListAPIView):
    """审核记录列表"""
    queryset = ReviewRecord.objects.all()
    serializer_class = ReviewRecordSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'is_auto', 'textbook']


class SensitiveWordListView(generics.ListCreateAPIView):
    """敏感词管理"""
    queryset = SensitiveWord.objects.all()
    serializer_class = SensitiveWordSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['word']

    def perform_create(self, serializer):
        serializer.save()
        reload_sensitive_filter()


class SensitiveWordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """敏感词详情/修改/删除"""
    queryset = SensitiveWord.objects.all()
    serializer_class = SensitiveWordSerializer
    permission_classes = [IsAdmin]

    def perform_update(self, serializer):
        serializer.save()
        reload_sensitive_filter()

    def perform_destroy(self, instance):
        instance.delete()
        reload_sensitive_filter()
