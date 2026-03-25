from django.db import models
from django.conf import settings


class Category(models.Model):
    """教材分类（支持多级分类）"""
    name = models.CharField('分类名称', max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name='children', verbose_name='父分类')
    level = models.IntegerField('层级', default=1)  # 1=学科, 2=课程, 3=教材类型
    sort_order = models.IntegerField('排序', default=0)
    is_active = models.BooleanField('是否启用', default=True)

    class Meta:
        db_table = 'categories'
        verbose_name = '分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Textbook(models.Model):
    """教材模型"""
    TRANSACTION_TYPE_CHOICES = (
        ('sell', '出售'),
        ('rent', '租赁'),
        ('free', '免费赠送'),
    )

    CONDITION_CHOICES = (
        (5, '全新'),
        (4, '九成新'),
        (3, '七成新'),
        (2, '五成新'),
        (1, '较旧'),
    )

    STATUS_CHOICES = (
        ('pending_review', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已驳回'),
        ('sold', '已售出'),
        ('rented', '已租出'),
        ('completed', '已完成'),
        ('offline', '已下架'),
    )

    title = models.CharField('书名', max_length=200)
    author = models.CharField('作者', max_length=200)
    isbn = models.CharField('ISBN', max_length=20, blank=True, default='')
    publisher = models.CharField('出版社', max_length=200, blank=True, default='')
    edition = models.CharField('版本/版次', max_length=50, blank=True, default='')
    condition = models.IntegerField('新旧程度', choices=CONDITION_CHOICES, default=4)
    description = models.TextField('描述', blank=True, default='')
    price = models.DecimalField('价格', max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField('原价', max_digits=10, decimal_places=2, null=True, blank=True)
    transaction_type = models.CharField('交易类型', max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='sell')
    rent_duration = models.IntegerField('租赁天数', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='textbooks', verbose_name='分类')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='textbooks', verbose_name='发布者')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending_review')
    cover_image = models.ImageField('封面图', upload_to='covers/', blank=True, null=True)
    view_count = models.IntegerField('浏览次数', default=0)
    created_at = models.DateTimeField('发布时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'textbooks'
        verbose_name = '教材'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.author}'


class TextbookVote(models.Model):
    """教材点赞/点踩"""
    VOTE_CHOICES = (
        (1, '点赞'),
        (-1, '点踩'),
    )
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE, related_name='votes', verbose_name='教材')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes', verbose_name='用户')
    vote = models.SmallIntegerField('投票', choices=VOTE_CHOICES)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'textbook_votes'
        verbose_name = '教材投票'
        verbose_name_plural = verbose_name
        unique_together = ('textbook', 'user')


class TextbookRating(models.Model):
    """教材星级评分（1-5分）"""
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE, related_name='ratings', verbose_name='教材')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='textbook_ratings', verbose_name='用户')
    score = models.PositiveSmallIntegerField('评分')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'textbook_ratings'
        verbose_name = '教材评分'
        verbose_name_plural = verbose_name
        unique_together = ('textbook', 'user')

    def __str__(self):
        return f'{self.user.username} -> {self.textbook.title}: {self.score}'


class TextbookComment(models.Model):
    """教材评论"""
    textbook = models.ForeignKey(Textbook, on_delete=models.CASCADE, related_name='comments', verbose_name='教材')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments', verbose_name='评论者')
    content = models.TextField('评论内容', max_length=500)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name='父评论')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'textbook_comments'
        verbose_name = '教材评论'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.content[:30]}'


class SharedResource(models.Model):
    """在线资料共享"""
    RESOURCE_TYPE_CHOICES = (
        ('pdf', 'PDF文档'),
        ('doc', 'Word文档'),
        ('ppt', 'PPT课件'),
        ('other', '其他'),
    )

    SALE_TYPE_CHOICES = (
        ('free', '免费'),
        ('sell', '售卖'),
    )

    title = models.CharField('标题', max_length=200)
    description = models.TextField('描述', blank=True, default='')
    file = models.FileField('文件', upload_to='resources/')
    file_size = models.IntegerField('文件大小(字节)', default=0)
    resource_type = models.CharField('类型', max_length=10, choices=RESOURCE_TYPE_CHOICES, default='pdf')
    sale_type = models.CharField('售卖类型', max_length=10, choices=SALE_TYPE_CHOICES, default='free')
    price = models.DecimalField('售价', max_digits=10, decimal_places=2, default=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='resources', verbose_name='分类')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='resources', verbose_name='上传者')
    download_count = models.IntegerField('下载次数', default=0)
    created_at = models.DateTimeField('上传时间', auto_now_add=True)

    class Meta:
        db_table = 'shared_resources'
        verbose_name = '共享资料'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ResourceOrder(models.Model):
    """在线资料订单"""
    STATUS_CHOICES = (
        ('pending', '待确认'),
        ('confirmed', '待支付'),
        ('paid_pending', '待卖家确认'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
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

    resource = models.ForeignKey(SharedResource, on_delete=models.CASCADE,
                                 related_name='orders', verbose_name='资料')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='resource_buy_orders', verbose_name='买家')
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                               related_name='resource_sell_orders', verbose_name='卖家')
    price = models.DecimalField('成交价格', max_digits=10, decimal_places=2, default=0)
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_qr = models.CharField('支付二维码链接', max_length=500, blank=True, default='')
    payment_qr_image = models.ImageField('支付二维码图片', upload_to='payment_qr/', blank=True, null=True)
    payment_proof = models.ImageField('支付凭证', upload_to='payment_proofs/', blank=True, null=True)
    note = models.TextField('备注', blank=True, default='')
    cancel_reason = models.CharField('取消原因', max_length=20, choices=CANCEL_REASON_CHOICES, blank=True, default='')
    cancel_by_role = models.CharField('取消发起方', max_length=10, choices=CANCEL_BY_CHOICES, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    confirmed_at = models.DateTimeField('确认时间', null=True, blank=True)
    paid_at = models.DateTimeField('支付时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)

    class Meta:
        db_table = 'resource_orders'
        verbose_name = '资料订单'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'资料订单#{self.id} {self.resource_id}'
