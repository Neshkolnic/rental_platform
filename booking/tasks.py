from celery import shared_task
from booking.utils import send_review_reminder_message

@shared_task
def schedule_review_reminder(booking_id):
    send_review_reminder_message(booking_id)

@shared_task
def test_celery(x, y):
    return x + y