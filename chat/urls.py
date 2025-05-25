from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_list_view, name='chat_list'),
    path('list/', views.chat_list_view, name='chat_list'),
    path('chats/', views.chat_list_view, name='chat_list'),
    path('chat/<int:booking_id>/', views.chat_room_view, name='chat_room'),
    path('room/<int:booking_id>/', views.chat_room_view, name='chat_room'),
    path('support/', views.support_chat_view, name='support_chat'),
path('room/<int:booking_id>/', views.chat_room_view, name='chat_room'),
    path('support/room/<int:chat_id>/', views.chat_room_view, name='support_chat_room'),
]
