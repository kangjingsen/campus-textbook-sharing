from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q

from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from apps.users.models import User


class ConversationListView(generics.ListAPIView):
    """会话列表"""
    serializer_class = ConversationSerializer

    def get_queryset(self):
        return self.request.user.conversations.all()


class ConversationCreateView(APIView):
    """创建或获取会话"""

    def post(self, request):
        other_user_id = request.data.get('user_id')
        if not other_user_id:
            return Response({'error': '请指定对方用户ID'}, status=status.HTTP_400_BAD_REQUEST)

        if int(other_user_id) == request.user.id:
            return Response({'error': '不能和自己聊天'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            other_user = User.objects.get(pk=other_user_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 查找已存在的会话
        conversations = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=other_user
        )

        if conversations.exists():
            conv = conversations.first()
        else:
            conv = Conversation.objects.create()
            conv.participants.add(request.user, other_user)

        serializer = ConversationSerializer(conv, context={'request': request})
        return Response(serializer.data)


class MessageListView(generics.ListAPIView):
    """会话消息历史"""
    serializer_class = MessageSerializer

    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        # 验证用户是会话参与者
        try:
            conv = Conversation.objects.get(
                id=conversation_id,
                participants=self.request.user
            )
        except Conversation.DoesNotExist:
            return Message.objects.none()

        # 标记为已读
        Message.objects.filter(
            conversation=conv,
            is_read=False
        ).exclude(sender=self.request.user).update(is_read=True)

        return conv.messages.all()


class SendMessageView(APIView):
    """通过 HTTP 发送消息（WebSocket 的备选方案）"""

    def post(self, request, conversation_id):
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': '消息不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            conv = Conversation.objects.get(
                id=conversation_id,
                participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response({'error': '会话不存在'}, status=status.HTTP_404_NOT_FOUND)

        message = Message.objects.create(
            conversation=conv,
            sender=request.user,
            content=content
        )

        return Response(MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class UnreadCountView(APIView):
    """获取未读消息总数"""

    def get(self, request):
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
        return Response({'unread_count': count})
