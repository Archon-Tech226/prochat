import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Channel, Message, DirectMessage


# ── Group Chat Consumer ───────────────────────────────────────────────────────
class GroupConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group  = f'chat_{self.channel_id}'
        self.user        = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data    = json.loads(text_data)
        content = data.get('message', '')

        if not content.strip():
            return

        # Save to MySQL
        message = await self.save_message(content)

        # Broadcast to all in group
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type':       'chat_message',
                'message':    content,
                'sender':     self.user.username,
                'sender_id':  self.user.id,
                'message_id': message.id,
                'timestamp':  message.created_at.strftime('%H:%M'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type':       'message',
            'message':    event['message'],
            'sender':     event['sender'],
            'sender_id':  event['sender_id'],
            'message_id': event['message_id'],
            'timestamp':  event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, content):
        channel = Channel.objects.get(id=self.channel_id)
        return Message.objects.create(
            channel=channel,
            sender=self.user,
            content=content
        )


# ── Typing Consumer ───────────────────────────────────────────────────────────
class TypingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.room_group  = f'typing_{self.channel_id}'
        self.user        = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data   = json.loads(text_data)
        typing = data.get('typing', False)

        await self.channel_layer.group_send(
            self.room_group,
            {
                'type':   'typing_status',
                'user':   self.user.username,
                'typing': typing,
            }
        )

    async def typing_status(self, event):
        if event['user'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type':   'typing',
                'user':   event['user'],
                'typing': event['typing'],
            }))


# ── DM Consumer ───────────────────────────────────────────────────────────────
class DMConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user      = self.scope['user']
        other_user_id  = self.scope['url_route']['kwargs']['user_id']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Consistent room name
        ids = sorted([self.user.id, int(other_user_id)])
        self.room_group  = f'dm_{ids[0]}_{ids[1]}'
        self.other_user_id = other_user_id

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data    = json.loads(text_data)
        content = data.get('message', '')

        if not content.strip():
            return

        message = await self.save_dm(content)

        await self.channel_layer.group_send(
            self.room_group,
            {
                'type':       'dm_message',
                'message':    content,
                'sender':     self.user.username,
                'sender_id':  self.user.id,
                'message_id': message.id,
                'timestamp':  message.created_at.strftime('%H:%M'),
            }
        )

    async def dm_message(self, event):
        await self.send(text_data=json.dumps({
            'type':       'message',
            'message':    event['message'],
            'sender':     event['sender'],
            'sender_id':  event['sender_id'],
            'message_id': event['message_id'],
            'timestamp':  event['timestamp'],
        }))

    @database_sync_to_async
    def save_dm(self, content):
        receiver = User.objects.get(id=self.other_user_id)
        return DirectMessage.objects.create(
            sender=self.user,
            receiver=receiver,
            content=content
        )


# ── Presence Consumer ─────────────────────────────────────────────────────────
class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group = 'presence'
        await self.set_online(True)
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'presence_update', 'user': self.user.username, 'online': True}
        )

    async def disconnect(self, close_code):
        await self.set_online(False)
        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'presence_update', 'user': self.user.username, 'online': False}
        )
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        pass

    async def presence_update(self, event):
        await self.send(text_data=json.dumps({
            'type':   'presence',
            'user':   event['user'],
            'online': event['online'],
        }))

    @database_sync_to_async
    def set_online(self, status):
        from accounts.models import UserProfile
        UserProfile.objects.filter(user=self.user).update(is_online=status)