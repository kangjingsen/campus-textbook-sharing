from rest_framework import serializers
from .models import ReviewRecord, SensitiveWord


class ReviewRecordSerializer(serializers.ModelSerializer):
    textbook_title = serializers.CharField(source='textbook.title', read_only=True)
    reviewer_name = serializers.CharField(source='reviewer.username', read_only=True, default='系统')

    class Meta:
        model = ReviewRecord
        fields = ['id', 'textbook', 'textbook_title', 'reviewer', 'reviewer_name',
                  'status', 'reason', 'sensitive_words_found', 'is_auto', 'reviewed_at']
        read_only_fields = ['id', 'reviewer', 'is_auto', 'reviewed_at', 'sensitive_words_found']


class ReviewActionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    reason = serializers.CharField(required=False, default='', allow_blank=True)


class SensitiveWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensitiveWord
        fields = ['id', 'word', 'category', 'is_active', 'created_at']
