from django.contrib import admin
from .models import Category, Textbook, TextbookVote, TextbookComment, SharedResource

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'level', 'sort_order', 'is_active']
    list_filter = ['level', 'is_active']

@admin.register(Textbook)
class TextbookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'price', 'transaction_type', 'status', 'owner', 'created_at']
    list_filter = ['status', 'transaction_type', 'condition', 'category']
    search_fields = ['title', 'author', 'isbn']

@admin.register(TextbookVote)
class TextbookVoteAdmin(admin.ModelAdmin):
    list_display = ['textbook', 'user', 'vote', 'created_at']
    list_filter = ['vote']

@admin.register(TextbookComment)
class TextbookCommentAdmin(admin.ModelAdmin):
    list_display = ['textbook', 'user', 'content', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content']

@admin.register(SharedResource)
class SharedResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'resource_type', 'uploader', 'download_count', 'created_at']
    list_filter = ['resource_type', 'category']
    search_fields = ['title', 'description']
