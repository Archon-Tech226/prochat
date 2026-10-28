from django.urls import path
from . import views

urlpatterns = [
    path('',                                         views.group_list,          name='group_list'),
    path('dm/',                                      views.dm_list,             name='dm_list'),
    path('channel/<int:channel_id>/',                views.channel_view,        name='channel_view'),
    path('dm/<int:user_id>/',                        views.dm_view,             name='dm_view'),
    path('create-group/',                            views.create_group,        name='create_group'),
    path('group/<int:group_id>/',                    views.group_detail,        name='group_detail'),
    path('group/<int:group_id>/add-member/',         views.add_member_by_email, name='add_member'),
    path('group/<int:group_id>/remove/<int:user_id>/', views.remove_member,    name='remove_member'),
    path('group/<int:group_id>/leave/',              views.leave_group,         name='leave_group'),
    path('group/<int:group_id>/channel/',            views.create_channel,      name='create_channel'),
    path('group/<int:group_id>/regenerate-invite/',  views.regenerate_invite,   name='regenerate_invite'),
    path('group/<int:group_id>/invite-link/',        views.get_invite_link,     name='get_invite_link'),
    path('join/<uuid:token>/',                       views.join_via_invite,     name='join_via_invite'),
]