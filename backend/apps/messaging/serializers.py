from rest_framework import serializers
from .models import Conversation, Message
from apps.users.serializers import UserSerializer


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.ImageField(source='sender.avatar', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender', 'sender_name', 'sender_avatar',
                  'content', 'is_read', 'created_at']
        read_only_fields = ['id', 'sender', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_user = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'last_message', 'unread_count',
                  'other_user', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        msg = obj.get_last_message()
        if msg:
            return MessageSerializer(msg).data
        return None

    def get_unread_count(self, obj):
        user = self.context.get('request').user
        return obj.get_unread_count(user)

    def get_other_user(self, obj):
        user = self.context.get('request').user
        other = obj.participants.exclude(id=user.id).first()
        if other:
            return {
                'id': other.id,
                'username': other.username,
                'avatar': other.avatar.url if other.avatar else None,
                'college': other.college,
            }
        return None
