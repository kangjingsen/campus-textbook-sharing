from django.apps import AppConfig


class TextbooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.textbooks'
    verbose_name = '教材管理'
