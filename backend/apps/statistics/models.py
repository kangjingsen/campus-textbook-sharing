from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

User = get_user_model()


class SellerRating(models.Model):
    """卖家评分记录"""
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    score = models.DecimalField(
        '评分',
        max_digits=3,
        decimal_places=1,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('5'))]
    )
    comment = models.CharField('评价内容', max_length=200, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'statistics_seller_ratings'
        verbose_name = '卖家评分'
        verbose_name_plural = verbose_name
        unique_together = ('seller', 'rater')  # 每个卖家只能被某个评价者评一次

    def __str__(self):
        return f'{self.rater.username} → {self.seller.username}: {self.score}分'
