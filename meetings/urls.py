from django.urls import path
from . import views

urlpatterns = [
    path('',                          views.meeting_list,    name='meeting_list'),
    path('create/',                   views.create_meeting,  name='create_meeting'),
    path('<uuid:meeting_id>/',        views.meeting_room,    name='meeting_room'),
    path('<uuid:meeting_id>/summary/', views.meeting_summary, name='meeting_summary'),
]