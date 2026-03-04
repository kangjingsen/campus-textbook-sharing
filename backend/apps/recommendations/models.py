from django.db import models
from django.conf import settings


class BrowsingHistory(models.Model):
    """用户浏览历史"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='browsing_history', verbose_name='用户')
    textbook = models.ForeignKey('textbooks.Textbook', on_delete=models.CASCADE,
                                 related_name='browsing_records', verbose_name='教材')
    view_count = models.IntegerField('浏览次数', default=1)
    last_viewed_at = models.DateTimeField('最后浏览时间', auto_now=True)
    created_at = models.DateTimeField('首次浏览时间', auto_now_add=True)

    class Meta:
        db_table = 'browsing_history'
        verbose_name = '浏览历史'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'textbook']

    def __str__(self):
        return f'{self.user.username} -> {self.textbook.title}'


class UserPreference(models.Model):
    """用户偏好分数"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='preferences', verbose_name='用户')
    category = models.ForeignKey('textbooks.Category', on_delete=models.CASCADE,
                                 related_name='user_preferences', verbose_name='分类')
    score = models.FloatField('偏好分数', default=0.0)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = '用户偏好'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'category']

    def __str__(self):
        return f'{self.user.username} -> {self.category.name}: {self.score}'


class RecommendationCache(models.Model):
    """推荐结果缓存"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='recommendation_cache', verbose_name='用户')
    textbook = models.ForeignKey('textbooks.Textbook', on_delete=models.CASCADE,
                                 verbose_name='推荐教材')
    score = models.FloatField('推荐分数', default=0.0)
    reason = models.CharField('推荐理由', max_length=200, default='')
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'recommendation_cache'
        verbose_name = '推荐缓存'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'textbook']
        ordering = ['-score']
