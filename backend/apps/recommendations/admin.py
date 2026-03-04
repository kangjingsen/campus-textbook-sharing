from django.contrib import admin
from .models import BrowsingHistory, UserPreference, RecommendationCache

@admin.register(BrowsingHistory)
class BrowsingHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'textbook', 'view_count', 'last_viewed_at']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'score', 'updated_at']

@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    list_display = ['user', 'textbook', 'score', 'reason', 'updated_at']
