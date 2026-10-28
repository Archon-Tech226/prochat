import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user       = self.scope['user']
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group  = f'meeting_{self.meeting_id}'

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'user_joined', 'user': self.user.username}
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.room_group,
            {'type': 'user_left', 'user': self.user.username}
        )
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('action') == 'end_meeting':
            await self.end_meeting()
            from meetings.tasks import summarise_meeting
            summarise_meeting.delay(self.meeting_id)

    async def user_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user'],
        }))

    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user'],
        }))

    async def meeting_summary(self, event):
        await self.send(text_data=json.dumps({
            'type':         'summary',
            'summary':      event['summary'],
            'action_items': event['action_items'],
        }))

    @database_sync_to_async
    def end_meeting(self):
        from meetings.models import Meeting
        from django.utils import timezone
        Meeting.objects.filter(id=self.meeting_id).update(ended_at=timezone.now())


class TranscriptConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user       = self.scope['user']
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.room_group  = f'transcript_{self.meeting_id}'

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data    = json.loads(text_data)
        caption = data.get('caption', '')

        if caption:
            await self.save_transcript(caption)
            await self.channel_layer.group_send(
                self.room_group,
                {'type': 'transcript_update', 'caption': caption, 'user': self.user.username}
            )

    async def transcript_update(self, event):
        await self.send(text_data=json.dumps({
            'type':    'transcript',
            'caption': event['caption'],
            'user':    event['user'],
        }))

    @database_sync_to_async
    def save_transcript(self, caption):
        from meetings.models import Meeting
        meeting = Meeting.objects.get(id=self.meeting_id)
        meeting.transcript = (meeting.transcript or '') + f'\n{self.user.username}: {caption}'
        meeting.save()