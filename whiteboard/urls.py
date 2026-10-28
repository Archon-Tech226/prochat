from django.urls import path
from . import views

urlpatterns = [
    path('create/',         views.create_board, name='create_board'),
    path('<int:board_id>/', views.board_view,   name='board_view'),
]