import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Chat, Message
from booking.models import Booking
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.room_group_name = f'chat_{self.booking_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = self.scope['user'].id

        booking = await self.get_booking()
        chat = await self.get_chat(booking)

        sender = await self.get_user(sender_id)
        msg = await self.create_message(chat, sender, message)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': msg.content,
                'sender': sender.username,
                'created_at': msg.created_at.strftime('%d %b %Y %H:%M'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_booking(self):
        return Booking.objects.get(id=self.booking_id)

    @database_sync_to_async
    def get_chat(self, booking):
        chat, created = Chat.objects.get_or_create(
            booking=booking,
            defaults={
                'tenant': booking.tenant,
                'landlord': booking.property.owner
            }
        )
        return chat

    @database_sync_to_async
    def create_message(self, chat, sender, content):
        return Message.objects.create(chat=chat, sender=sender, content=content)

    @database_sync_to_async
    def get_user(self, user_id):
        return User.objects.get(id=user_id)
