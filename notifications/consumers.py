import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        self.room_group = f'notifications_{self.user.id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # ── Safe unread count — ignore if Redis not ready ──
        try:
            count = await self.get_unread_count()
            await self.send(text_data=json.dumps({
                'type':  'unread_count',
                'count': count,
            }))
        except Exception:
            pass

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group, self.channel_name)
        except Exception:
            pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get('action') == 'mark_read':
                await self.mark_all_read()
                await self.send(text_data=json.dumps({'type': 'unread_count', 'count': 0}))
        except Exception:
            pass

    async def send_notification(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type':       'notification',
                'title':      event['title'],
                'body':       event['body'],
                'notif_type': event['notif_type'],
                'link':       event.get('link', ''),
            }))
        except Exception:
            pass

    async def badge_update(self, event):
        try:
            await self.send(text_data=json.dumps({
                'type':  'unread_count',
                'count': event['count'],
            }))
        except Exception:
            pass

    @database_sync_to_async
    def get_unread_count(self):
        from .models import Notification
        return Notification.objects.filter(user=self.user, is_read=False).count()

    @database_sync_to_async
    def mark_all_read(self):
        from .models import Notification
        Notification.objects.filter(user=self.user, is_read=False).update(is_read=True)