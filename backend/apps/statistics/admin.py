from django.contrib import admin
from .models import SellerRating


@admin.register(SellerRating)
class SellerRatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'seller', 'rater', 'score', 'comment', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('seller__username', 'rater__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')
