# tasks/routing.py
from django.urls import re_path
from tasks import consumers as task_consumers

websocket_urlpatterns = [
    re_path(r'ws/tasks/$', task_consumers.TaskConsumer.as_asgi()),
]