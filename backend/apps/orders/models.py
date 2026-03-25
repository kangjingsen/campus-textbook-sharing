import uuid
from django.db import models
from django.conf import settings


class Order(models.Model):
    """订单模型"""
    STATUS_CHOICES = (
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
        ('returned', '已归还'),
    )

    CANCEL_REASON_CHOICES = (
        ('price', '价格不合适'),
        ('schedule', '无法线下交易'),
        ('duplicate', '重复下单'),
        ('not_needed', '暂时不需要'),
        ('unresponsive', '对方长时间未响应'),
        ('other', '其他'),
    )

    CANCEL_BY_CHOICES = (
        ('buyer', '买家'),
        ('seller', '卖家'),
        ('system', '系统'),
    )

    order_no = models.CharField('订单号', max_length=32, unique=True, editable=False)
    textbook = models.ForeignKey('textbooks.Textbook', on_delete=models.CASCADE,
                                 related_name='orders', verbose_name='教材')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='buy_orders', verbose_name='买方')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='sell_orders', verbose_name='卖方')
    transaction_type = models.CharField('交易类型', max_length=10)
    price = models.DecimalField('成交价格', max_digits=10, decimal_places=2)
    status = models.CharField('订单状态', max_length=10, choices=STATUS_CHOICES, default='pending')
    rent_start_date = models.DateField('租赁开始日期', null=True, blank=True)
    rent_end_date = models.DateField('租赁结束日期', null=True, blank=True)
    note = models.TextField('备注', blank=True, default='')
    cancel_reason = models.CharField('取消原因', max_length=20, choices=CANCEL_REASON_CHOICES, blank=True, default='')
    cancel_by_role = models.CharField('取消发起方', max_length=10, choices=CANCEL_BY_CHOICES, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'orders'
        verbose_name = '订单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_no:
            self.order_no = uuid.uuid4().hex[:16].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'订单 {self.order_no}'
