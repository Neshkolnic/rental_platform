from django.urls import path
from . import views

urlpatterns = [
    # Путь для чата с определённым бронированием
    path('chats/', views.chat_list_view, name='chat_list'),
    path('chat/<int:booking_id>/', views.chat_room_view, name='chat_room'),
]