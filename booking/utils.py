# booking/utils.py (или chat/utils.py)
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.urls import reverse
from chat.models import Chat, Message
from booking.models import Booking
from django.contrib.auth import get_user_model

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

    # Создаем сообщение от системного юзера
    msg = Message.objects.create(chat=chat, sender=system_user, content=message_text)

    # Отправляем уведомление в WebSocket группу
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'chat_{booking_id}', {
            'type': 'chat_message',
            'message': msg.content,
            'sender': system_user.username,
            'created_at': msg.created_at.strftime('%d %b %Y %H:%M'),
        }
    )
