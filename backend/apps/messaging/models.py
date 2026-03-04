from django.db import models
from django.conf import settings


class Conversation(models.Model):
    """会话"""
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          related_name='conversations', verbose_name='参与者')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('最后消息时间', auto_now=True)

    class Meta:
        db_table = 'conversations'
        verbose_name = '会话'
        verbose_name_plural = verbose_name
        ordering = ['-updated_at']

    def __str__(self):
        return f'会话 #{self.id}'

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """消息"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name='messages', verbose_name='会话')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='sent_messages', verbose_name='发送者')
    content = models.TextField('消息内容')
    is_read = models.BooleanField('是否已读', default=False)
    created_at = models.DateTimeField('发送时间', auto_now_add=True)

    class Meta:
        db_table = 'messages'
        verbose_name = '消息'
        verbose_name_plural = verbose_name
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:30]}'
