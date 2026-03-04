from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.textbooks.models import Textbook
from .sensitive_filter import check_sensitive
from .models import ReviewRecord


@receiver(post_save, sender=Textbook)
def auto_check_sensitive(sender, instance, created, **kwargs):
    """教材创建时自动进行敏感词审核：无敏感词自动通过，有敏感词自动驳回"""
    if not created:
        return

    # 合并所有需要检测的文本
    text_to_check = f"{instance.title} {instance.author} {instance.description}"
    has_sensitive, words = check_sensitive(text_to_check)

    if has_sensitive:
        # 自动标记并创建审核记录 — 驳回
        ReviewRecord.objects.create(
            textbook=instance,
            reviewer=None,
            status='rejected',
            reason=f'自动检测到敏感词：{", ".join(words)}',
            sensitive_words_found=', '.join(words),
            is_auto=True
        )
        Textbook.objects.filter(pk=instance.pk).update(status='rejected')
    else:
        # 无敏感词，自动审核通过
        ReviewRecord.objects.create(
            textbook=instance,
            reviewer=None,
            status='approved',
            reason='自动审核通过：未检测到敏感词',
            sensitive_words_found='',
            is_auto=True
        )
        Textbook.objects.filter(pk=instance.pk).update(status='approved')
