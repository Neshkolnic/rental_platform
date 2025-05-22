from django.db import models
from django.conf import settings  # для AUTH_USER_MODEL
from booking.models import Booking  # импортируем модель бронирования

class Chat(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='tenant_chats',
        on_delete=models.CASCADE
    )
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='landlord_chats',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for booking {self.booking.id}"


class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        related_name='messages',
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username} at {self.created_at}"
