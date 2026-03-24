from rest_framework import serializers
from .models import SellerRating
from django.contrib.auth import get_user_model

User = get_user_model()


class SellerRatingSerializer(serializers.ModelSerializer):
    """卖家评分序列化器"""
    seller_name = serializers.CharField(source='seller.username', read_only=True)
    rater_name = serializers.CharField(source='rater.username', read_only=True)

    class Meta:
        model = SellerRating
        fields = ['id', 'seller', 'seller_name', 'rater', 'rater_name', 'score', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'rater', 'created_at', 'updated_at']

    def create(self, validated_data):
        # 自动设置当前用户为评分人
        validated_data['rater'] = self.context['request'].user
        return super().create(validated_data)
