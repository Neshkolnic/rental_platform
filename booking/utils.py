# booking/utils.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.urls import reverse
from chat.models import Chat, Message
from booking.models import Booking
from django.contrib.auth import get_user_model
import requests
import os

User = get_user_model()

def get_system_user():
    system_user, created = User.objects.get_or_create(
        email='no-reply@bookingapp.com',
        defaults={
            'username': 'system',
            'first_name': 'System',
            'last_name': 'Bot',
            'role': User.Role.ADMIN,
            'is_verified': True,
            'password': '',
        }
    )
    if created:
        system_user.set_unusable_password()
        system_user.save()
    return system_user

def send_review_reminder_message(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return

    tenant = booking.tenant
    landlord = booking.property.owner

    chat = Chat.objects.filter(booking=booking).first()
    if not chat:
        chat = Chat.objects.create(
            booking=booking,
            tenant=tenant,
            landlord=landlord,
            is_support_chat=False
        )

    system_user = get_system_user()

    url_landlord = reverse('leave_review_landlord', args=[booking_id])
    url_tenant = reverse('leave_review_tenant', args=[booking_id])
    url_property = reverse('leave_review_property', args=[booking_id])

    message_text = (
        "Ваше бронирование завершено! Пожалуйста, оставьте отзывы друг о друге и об объекте.\n"
        f"Арендатор, оставьте отзыв о собственнике здесь: http://127.0.0.1:8000{url_landlord}\n"
        f"Собственник, оставьте отзыв об арендаторе здесь: http://127.0.0.1:8000{url_tenant}\n"
        f"Арендатор, оставьте отзыв об объекте здесь: http://127.0.0.1:8000{url_property}"
    )

    msg = Message.objects.create(chat=chat, sender=system_user, content=message_text)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{booking_id}', {
            'type': 'chat_message',
            'message': msg.content,
            'sender': system_user.username,
            'created_at': msg.created_at.strftime('%d %b %Y %H:%M'),
        }
    )

    telegram_message = (
        "📢 Ваше бронирование завершено!\n\n"
        "Пожалуйста, оставьте отзывы:\n"
        f"👤 О владельце: http://127.0.0.1:8000{url_landlord}\n"
        f"🏠 Об объекте: http://127.0.0.1:8000{url_property}\n"
        f"👤 О арендаторе (для владельца): http://127.0.0.1:8000{url_tenant}"
    )

    if tenant.telegram_id:
        send_telegram_notification(tenant.telegram_id, telegram_message)

    if landlord.telegram_id:
        send_telegram_notification(landlord.telegram_id, telegram_message)


def send_telegram_notification(telegram_id, message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")  # Бот-токен должен быть в переменных окружения
    if not token:
        print("TELEGRAM_BOT_TOKEN не найден в переменных окружения.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка при отправке Telegram-сообщения: {e}")


import hashlib
import requests
import random
import string
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))
def send_sms(phone, message):
    rocketsms_login = '998348819'  # 998348819
    rocketsms_password = 'kpYPWJe9'  # kpYPWJe9
    rocketsms_passhash = hashlib.md5(rocketsms_password.encode('utf-8')).hexdigest()
    rocketsms_url = 'http://api.rocketsms.by/simple/send'

    data = {
        'username': rocketsms_login,
        'password': rocketsms_passhash,
        'phone': phone,
        'text': message,
        'priority': 'true'
    }
    try:
        request = requests.post(rocketsms_url, data=data)
        result = request.json()
        status = result['status']
    except Exception as e:
        print(f'Error: {e}')
    else:
        if status in ['SENT', 'QUEUED']:
            print(f'SMS sent: {status}')
        else:
            print(f'SMS failed: {status}')

from django.core.mail import send_mail
from django.conf import settings

def send_verification_code(to_email, code):
    subject = 'Код подтверждения смены почты'
    message = f'Ваш код подтверждения: {code}'
    from_email = settings.DEFAULT_FROM_EMAIL
    send_mail(subject, message, from_email, [to_email])
