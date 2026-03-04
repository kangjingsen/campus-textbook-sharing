from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """扩展用户模型"""
    ROLE_CHOICES = (
        ('student', '学生'),
        ('admin', '管理员'),
        ('superadmin', '超级管理员'),
    )

    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField('学号', max_length=20, blank=True, default='')
    college = models.CharField('学院', max_length=100, blank=True, default='')
    major = models.CharField('专业', max_length=100, blank=True, default='')
    phone = models.CharField('手机号', max_length=11, blank=True, default='')
    avatar = models.ImageField('头像', upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField('是否已验证', default=False)
    bio = models.TextField('个人简介', blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
