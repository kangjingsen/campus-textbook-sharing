from django.conf import settings
from django.db import models
from django.utils import timezone


class Announcement(models.Model):
    title = models.CharField('标题', max_length=200)
    summary = models.CharField('摘要', max_length=300, blank=True, default='')
    content = models.TextField('正文')
    is_pinned = models.BooleanField('置顶', default=False)
    is_active = models.BooleanField('是否启用', default=True)
    published_at = models.DateTimeField('发布时间', default=timezone.now)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'community_announcements'
        ordering = ['-is_pinned', '-published_at', '-id']

    def __str__(self):
        return self.title


class ForumTopic(models.Model):
    TOPIC_TYPE_CHOICES = (
        ('discussion', '讨论'),
        ('question', '问答'),
    )

    title = models.CharField('标题', max_length=220)
    content = models.TextField('内容')
    topic_type = models.CharField('帖子类型', max_length=20, choices=TOPIC_TYPE_CHOICES, default='discussion')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_topics')
    is_pinned = models.BooleanField('置顶', default=False)
    is_locked = models.BooleanField('锁定', default=False)
    view_count = models.PositiveIntegerField('浏览量', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    last_activity_at = models.DateTimeField('最后活跃时间', auto_now=True)

    class Meta:
        db_table = 'community_forum_topics'
        ordering = ['-is_pinned', '-last_activity_at', '-id']

    def __str__(self):
        return self.title


class ForumReply(models.Model):
    topic = models.ForeignKey(ForumTopic, on_delete=models.CASCADE, related_name='replies')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='forum_replies')
    content = models.TextField('回复内容')
    is_best_answer = models.BooleanField('最佳回答', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'community_forum_replies'
        ordering = ['created_at', 'id']

    def __str__(self):
        return f'{self.topic_id}-{self.user_id}'
