from django.contrib import admin

from .models import Announcement, ForumTopic, ForumReply


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_pinned', 'is_active', 'published_at')
    list_filter = ('is_pinned', 'is_active')
    search_fields = ('title', 'summary')


@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'topic_type', 'creator', 'is_pinned', 'is_locked', 'view_count', 'created_at')
    list_filter = ('topic_type', 'is_pinned', 'is_locked')
    search_fields = ('title', 'content')


@admin.register(ForumReply)
class ForumReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'topic', 'user', 'is_best_answer', 'created_at')
    list_filter = ('is_best_answer',)
    search_fields = ('content',)
