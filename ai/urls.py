from django.urls import path
from . import views

urlpatterns = [
    path('',           views.ai_chat,           name='ai_chat'),
    path('stream/',    views.stream_response,    name='ai_stream'),
    path('translate/', views.translate_message,  name='ai_translate'),
    path('summarise/', views.summarise_document, name='ai_summarise'),
]