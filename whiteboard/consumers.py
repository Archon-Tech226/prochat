import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class WhiteboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user     = self.scope['user']
        self.board_id = self.scope['url_route']['kwargs']['board_id']
        self.room_group = f'whiteboard_{self.board_id}'

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

        # Send existing strokes
        strokes = await self.get_strokes()
        await self.send(text_data=json.dumps({'type': 'existing_strokes', 'strokes': strokes}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'stroke':
            await self.save_stroke(data['stroke'])
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type':   'stroke_update',
                    'stroke': data['stroke'],
                    'user':   self.user.username,
                }
            )

        elif data.get('type') == 'clear':
            await self.clear_board()
            await self.channel_layer.group_send(
                self.room_group,
                {'type': 'board_cleared', 'user': self.user.username}
            )

    async def stroke_update(self, event):
        await self.send(text_data=json.dumps({
            'type':   'stroke',
            'stroke': event['stroke'],
            'user':   event['user'],
        }))

    async def board_cleared(self, event):
        await self.send(text_data=json.dumps({'type': 'cleared'}))

    @database_sync_to_async
    def get_strokes(self):
        from .models import BoardStroke
        strokes = BoardStroke.objects.filter(board_id=self.board_id).order_by('created_at')
        return [s.stroke_data for s in strokes]

    @database_sync_to_async
    def save_stroke(self, stroke_data):
        from .models import BoardStroke
        BoardStroke.objects.create(
            board_id=self.board_id,
            user=self.user,
            stroke_data=stroke_data
        )

    @database_sync_to_async
    def clear_board(self):
        from .models import BoardStroke
        BoardStroke.objects.filter(board_id=self.board_id).delete()