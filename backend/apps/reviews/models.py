from django.db import models
from django.conf import settings


class SensitiveWord(models.Model):
    """敏感词库"""
    word = models.CharField('敏感词', max_length=100, unique=True)
    category = models.CharField('类别', max_length=50, default='political',
                                choices=[
                                    ('political', '政治敏感'),
                                    ('violence', '暴力'),
                                    ('illegal', '违法'),
                                    ('other', '其他'),
                                ])
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sensitive_words'
        verbose_name = '敏感词'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.word


class ReviewRecord(models.Model):
    """审核记录"""
    STATUS_CHOICES = (
        ('approved', '通过'),
        ('rejected', '驳回'),
    )

    textbook = models.ForeignKey('textbooks.Textbook', on_delete=models.CASCADE,
                                 related_name='review_records', verbose_name='教材')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, related_name='review_records', verbose_name='审核人')
    status = models.CharField('审核结果', max_length=10, choices=STATUS_CHOICES)
    reason = models.TextField('审核意见', blank=True, default='')
    sensitive_words_found = models.TextField('命中敏感词', blank=True, default='')
    is_auto = models.BooleanField('是否自动审核', default=False)
    reviewed_at = models.DateTimeField('审核时间', auto_now_add=True)

    class Meta:
        db_table = 'review_records'
        verbose_name = '审核记录'
        verbose_name_plural = verbose_name
        ordering = ['-reviewed_at']

    def __str__(self):
        return f'{self.textbook.title} - {self.get_status_display()}'
