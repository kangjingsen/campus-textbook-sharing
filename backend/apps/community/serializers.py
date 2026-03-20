from rest_framework import serializers
from django.db.models import Count

from .models import Announcement, ForumTopic, ForumReply


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = ['id', 'title', 'summary', 'content', 'is_pinned', 'is_active', 'published_at', 'created_at']


class ForumReplySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = ForumReply
        fields = ['id', 'topic', 'user', 'username', 'content', 'is_best_answer', 'created_at']
        read_only_fields = ['topic', 'user', 'is_best_answer', 'created_at']


class ForumTopicSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    reply_count = serializers.SerializerMethodField()
    latest_reply_at = serializers.SerializerMethodField()

    class Meta:
        model = ForumTopic
        fields = [
            'id', 'title', 'content', 'topic_type', 'creator', 'creator_name',
            'is_pinned', 'is_locked', 'view_count', 'reply_count', 'latest_reply_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['creator', 'is_pinned', 'is_locked', 'view_count', 'created_at', 'updated_at']

    def get_reply_count(self, obj):
        return getattr(obj, 'reply_count', None) or obj.replies.count()

    def get_latest_reply_at(self, obj):
        latest = obj.replies.order_by('-created_at').values_list('created_at', flat=True).first()
        return latest


class ForumTopicListSerializer(ForumTopicSerializer):
    class Meta(ForumTopicSerializer.Meta):
        fields = [
            'id', 'title', 'topic_type', 'creator_name', 'is_pinned', 'is_locked',
            'view_count', 'reply_count', 'latest_reply_at', 'created_at'
        ]


class ForumTopicDetailSerializer(ForumTopicSerializer):
    replies = ForumReplySerializer(many=True, read_only=True)

    class Meta(ForumTopicSerializer.Meta):
        fields = ForumTopicSerializer.Meta.fields + ['replies']
