from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import WishlistItem
from .tasks import update_user_recommendations


@receiver(post_save, sender=WishlistItem)
def refresh_recommendations_on_wishlist_save(sender, instance, **kwargs):
    """心愿单新增/修改后刷新推荐缓存"""
    try:
        update_user_recommendations(instance.user_id)
    except Exception:
        pass


@receiver(post_delete, sender=WishlistItem)
def refresh_recommendations_on_wishlist_delete(sender, instance, **kwargs):
    """心愿单删除后刷新推荐缓存"""
    try:
        update_user_recommendations(instance.user_id)
    except Exception:
        pass
