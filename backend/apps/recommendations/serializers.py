from rest_framework import serializers
from .models import BrowsingHistory, RecommendationCache, WishlistItem
from apps.textbooks.serializers import TextbookListSerializer


class BrowsingHistorySerializer(serializers.ModelSerializer):
    textbook_title = serializers.CharField(source='textbook.title', read_only=True)
    textbook_cover = serializers.ImageField(source='textbook.cover_image', read_only=True)

    class Meta:
        model = BrowsingHistory
        fields = ['id', 'textbook', 'textbook_title', 'textbook_cover',
                  'view_count', 'last_viewed_at', 'created_at']


class RecommendationSerializer(serializers.ModelSerializer):
    textbook = TextbookListSerializer(read_only=True)

    class Meta:
        model = RecommendationCache
        fields = ['id', 'textbook', 'score', 'reason', 'updated_at']


class WishlistItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default='')

    class Meta:
        model = WishlistItem
        fields = [
            'id', 'title', 'author', 'isbn', 'category', 'category_name',
            'note', 'priority', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
