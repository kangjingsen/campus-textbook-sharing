from django.contrib import admin
from .models import ReviewRecord, SensitiveWord

@admin.register(ReviewRecord)
class ReviewRecordAdmin(admin.ModelAdmin):
    list_display = ['textbook', 'reviewer', 'status', 'is_auto', 'reviewed_at']
    list_filter = ['status', 'is_auto']

@admin.register(SensitiveWord)
class SensitiveWordAdmin(admin.ModelAdmin):
    list_display = ['word', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['word']
