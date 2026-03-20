from django.db.models import F, Count
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from utils.permissions import IsAdmin
from .models import Announcement, ForumTopic, ForumReply
from .serializers import (
    AnnouncementSerializer,
    ForumTopicListSerializer,
    ForumTopicDetailSerializer,
    ForumReplySerializer,
)


class AnnouncementListView(generics.ListAPIView):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Announcement.objects.filter(is_active=True)


class AnnouncementManageListCreateView(generics.ListCreateAPIView):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    permission_classes = [IsAdmin]


class AnnouncementManageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AnnouncementSerializer
    queryset = Announcement.objects.all()
    permission_classes = [IsAdmin]


class ForumTopicListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ForumTopicListSerializer
        return ForumTopicDetailSerializer

    def get_queryset(self):
        qs = ForumTopic.objects.all().annotate(reply_count=Count('replies'))
        topic_type = self.request.query_params.get('topic_type')
        keyword = self.request.query_params.get('q', '').strip()
        if topic_type:
            qs = qs.filter(topic_type=topic_type)
        if keyword:
            qs = qs.filter(title__icontains=keyword)
        return qs

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class ForumTopicDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ForumTopicDetailSerializer
    queryset = ForumTopic.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        ForumTopic.objects.filter(pk=instance.pk).update(view_count=F('view_count') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id != instance.creator_id and request.user.role not in ('admin', 'superadmin'):
            return Response({'detail': '无权限编辑该帖子'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.id != instance.creator_id and request.user.role not in ('admin', 'superadmin'):
            return Response({'detail': '无权限删除该帖子'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class ForumReplyListCreateView(generics.ListCreateAPIView):
    serializer_class = ForumReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return ForumReply.objects.filter(topic_id=self.kwargs['topic_id'])

    def perform_create(self, serializer):
        try:
            topic = ForumTopic.objects.get(pk=self.kwargs['topic_id'])
        except ForumTopic.DoesNotExist:
            raise ValidationError('主题不存在')
        if topic.is_locked:
            raise ValidationError('该帖子已锁定，无法回复')
        serializer.save(user=self.request.user, topic=topic)


class ForumBestAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, topic_id, reply_id):
        try:
            topic = ForumTopic.objects.get(pk=topic_id)
            reply = ForumReply.objects.get(pk=reply_id, topic_id=topic_id)
        except (ForumTopic.DoesNotExist, ForumReply.DoesNotExist):
            return Response({'detail': '主题或回复不存在'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.id != topic.creator_id and request.user.role not in ('admin', 'superadmin'):
            return Response({'detail': '无权限设置最佳答案'}, status=status.HTTP_403_FORBIDDEN)

        ForumReply.objects.filter(topic_id=topic_id, is_best_answer=True).update(is_best_answer=False)
        reply.is_best_answer = True
        reply.save(update_fields=['is_best_answer'])

        return Response({'message': '已设置最佳答案'})
