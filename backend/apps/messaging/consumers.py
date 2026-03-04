import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket 聊天消费者"""

    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope.get('user')

        if not self.user or self.user.is_anonymous:
            await self.close()
            return

        # 验证用户是否是会话参与者
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # 标记消息为已读
        await self.mark_messages_read()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')

        if message_type == 'message':
            content = data.get('content', '').strip()
            if not content:
                return

            # 保存消息到数据库
            message = await self.save_message(content)

            # 广播消息到房间
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'sender': self.user.id,
                        'sender_name': self.user.username,
                        'sender_avatar': self.user.avatar.url if self.user.avatar else None,
                        'content': content,
                        'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    }
                }
            )

        elif message_type == 'read':
            await self.mark_messages_read()

    async def chat_message(self, event):
        """发送消息到 WebSocket"""
        await self.send(text_data=json.dumps(event['message'], ensure_ascii=False))

    @database_sync_to_async
    def check_participant(self):
        try:
            conv = Conversation.objects.get(id=self.conversation_id)
            return conv.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        # 更新会话时间
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        return message

    @database_sync_to_async
    def mark_messages_read(self):
        Message.objects.filter(
            conversation_id=self.conversation_id,
            is_read=False
        ).exclude(sender=self.user).update(is_read=True)
