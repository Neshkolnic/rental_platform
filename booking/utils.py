import threading
import time
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
            'password': '',  # если поле требуется
        }
    )
    return system_user


def send_review_reminder_message(booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
    except Booking.DoesNotExist:
        return

    tenant = booking.tenant
    landlord = booking.property.owner

    # Найти чат по бронированию
    chat = Chat.objects.filter(booking=booking).first()
    if not chat:
        chat = Chat.objects.create(
            booking=booking,
            tenant=tenant,
            landlord=landlord,
            is_support_chat=False
        )

    system_user = get_system_user()

    message_text = (
        "Ваше бронирование завершено! Пожалуйста, оставьте отзыв друг о друге.\n"
        "Арендатор, вы можете оценить собственника квартиры.\n"
        "Собственник, вы можете оценить арендатора.\n"
        "Спасибо!"
    )

    Message.objects.create(
        chat=chat,
        sender=system_user,
        content=message_text
    )


def schedule_review_reminder(booking_id, delay_seconds=3):
    def task():
        time.sleep(delay_seconds)
        send_review_reminder_message(booking_id)

    threading.Thread(target=task).start()
