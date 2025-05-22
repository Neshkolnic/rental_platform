# your_app/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Booking, Message
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.room_group_name = f'chat_{self.booking_id}'

        # Добавляем в группу
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Удаляем из группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Получаем сообщение от WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = self.scope["user"].id
        booking_id = self.booking_id

        # Сохраняем сообщение в БД
        await self.save_message(sender_id, booking_id, message)

        # Шлем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': self.scope["user"].full_name,
            }
        )

    # Отправка в WebSocket
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
        }))

    @database_sync_to_async
    def save_message(self, sender_id, booking_id, message):
        booking = Booking.objects.get(id=booking_id)
        sender = User.objects.get(id=sender_id)
        receiver = booking.property.owner if sender == booking.tenant else booking.tenant
        Message.objects.create(sender=sender, receiver=receiver, booking=booking, text=message)
