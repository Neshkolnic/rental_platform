from django.contrib.auth import get_user_model

User = get_user_model()

def get_system_user():
    system_user, created = User.objects.get_or_create(
        email='no-reply@bookingapp.com',
        defaults={
            'username': 'system',
            'first_name': 'System',
            'last_name': 'Bot',
            'role': User.Role.ADMIN,  # если есть роль, подстрой под себя
            'is_verified': True,
            'password': '',
        }
    )
    if created:
        system_user.set_unusable_password()  # запретить вход
        system_user.save()
    return system_user

from chat.models import Chat, Message
from booking.models import Booking

from django.urls import reverse

def send_review_reminder_message(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return

    tenant = booking.tenant
    landlord = booking.property.owner

    # Найти чат по бронированию или создать новый
    chat = Chat.objects.filter(booking=booking).first()
    if not chat:
        chat = Chat.objects.create(
            booking=booking,
            tenant=tenant,
            landlord=landlord,
            is_support_chat=False
        )

    system_user = get_system_user()

    # Генерируем URL для оставления отзыва
    review_url = reverse('leave_review', args=[booking_id])
    full_review_url = f"http://127.0.0.1:8000{review_url}"  # Замените yourdomain.com на реальный домен

    message_text = (
        "Ваше бронирование завершено! Пожалуйста, оставьте отзыв друг о друге.\n"
        f"Арендатор, вы можете оценить собственника квартиры здесь: {full_review_url}\n"
        f"Собственник, вы можете оценить арендатора здесь: {full_review_url}\n"
        "Спасибо!"
    )

    Message.objects.create(
        chat=chat,
        sender=system_user,
        content=message_text
    )


import threading
import time

def schedule_review_reminder(booking_id, delay_seconds=3):
    def task():
        time.sleep(delay_seconds)
        send_review_reminder_message(booking_id)

    threading.Thread(target=task).start()
