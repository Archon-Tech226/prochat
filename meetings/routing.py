# meetings/routing.py
from django.urls import re_path
from meetings import consumers as meeting_consumers

websocket_urlpatterns = [
    re_path(r'ws/meeting/(?P<meeting_id>[0-9a-f-]+)/$', meeting_consumers.MeetingConsumer.as_asgi()),
    re_path(r'ws/transcript/(?P<meeting_id>[0-9a-f-]+)/$', meeting_consumers.TranscriptConsumer.as_asgi()),
]