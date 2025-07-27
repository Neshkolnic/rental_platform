# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Chat, Message
from booking.models import Booking
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from adminpanel.models import SupportAssignment
from chat.tasks import send_system_notification
from chat.tasks import send_system_notification
from chat.models import Chat
from channels.db import database_sync_to_async

from chat.tasks import send_system_notification

from chat.tasks import send_system_notification
from chat.models import Chat
from channels.db import database_sync_to_async

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.room_group_name = f'chat_{self.booking_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        user = self.scope['user']
        if not user.is_authenticated:
            return

        # Определяем текст уведомления
        text = await self.get_notification_text(user)

        # Запускаем задачу через 3 секунды
        if text:
            send_system_notification.apply_async(args=[self.booking_id, text], countdown=3)

    @database_sync_to_async
    def get_notification_text(self, user):
        """
        Определяет, какое уведомление отправить пользователю.
        """
        try:
            chat = Chat.objects.get(booking_id=self.booking_id)
        except Chat.DoesNotExist:
            return None

        if chat.landlord == user:
            return "Пожалуйста, оцените арендатора."
        elif chat.tenant == user:
            return "Пожалуйста, оцените жильё."
        return None


    @database_sync_to_async
    def get_notification_text(self, user):
        """
        Определяет, какое уведомление отправить пользователю.
        """
        try:
            chat = Chat.objects.get(booking_id=self.booking_id)
        except Chat.DoesNotExist:
            return None

        if chat.landlord == user:
            return "Пожалуйста, оцените арендатора."
        elif chat.tenant == user:
            return "Пожалуйста, оцените жильё."
        return None

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        sender = self.scope['user']

        if not sender.is_authenticated or not message:
            return

        booking = await self.get_booking()
        chat = await self.get_chat(booking)
        msg = await self.create_message(chat, sender, message)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': msg.content,
            'sender': sender.username,
            'created_at': msg.created_at.strftime('%d %b %Y %H:%M'),
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_booking(self):
        return Booking.objects.get(id=self.booking_id)

    @database_sync_to_async
    def get_chat(self, booking):
        chat, _ = Chat.objects.get_or_create(
            booking=booking,
            defaults={'tenant': booking.tenant, 'landlord': booking.property.owner}
        )
        return chat

    @database_sync_to_async
    def create_message(self, chat, sender, content):
        return Message.objects.create(chat=chat, sender=sender, content=content)


class SupportChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.room_group_name = f'support_{self.chat_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        sender = self.scope['user']

        if not sender.is_authenticated or not message:
            return

        chat = await self.get_chat()

        # Если чат закрыт — откроем и сбросим назначение саппорта
        if chat.is_closed:
            await self.open_chat(chat)

        msg = await self.create_message(chat, sender, message)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': msg.content,
            'sender': sender.username,
            'created_at': msg.created_at.strftime('%d %b %Y %H:%M'),
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_chat(self):
        return Chat.objects.get(id=self.chat_id)

    @database_sync_to_async
    def open_chat(self, chat):
        chat.is_closed = False
        chat.save()
        SupportAssignment.objects.filter(chat=chat).delete()

    @database_sync_to_async
    def create_message(self, chat, sender, content):
        return Message.objects.create(chat=chat, sender=sender, content=content)
