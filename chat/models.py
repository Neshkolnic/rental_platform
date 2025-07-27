from django.db import models
from django.conf import settings
from booking.models import Booking

User = settings.AUTH_USER_MODEL


class Chat(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, null=True, blank=True)
    tenant = models.ForeignKey(
        User,
        related_name='tenant_chats',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    landlord = models.ForeignKey(
        User,
        related_name='landlord_chats',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    is_support_chat = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_closed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        if self.booking:
            return f"Chat for booking {self.booking.id}"
        if self.is_support_chat:
            return f"Support chat for {self.tenant}"
        return f"Chat {self.id}"

class Message(models.Model):
    chat = models.ForeignKey(
        Chat,
        related_name='messages',
        on_delete=models.CASCADE
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,  # <- добавляем
        blank=True, # <- добавляем
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender or 'System'} at {self.created_at}"



class SupportAssignment(models.Model):
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE)
    support = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_support_assignments')
    is_resolved = models.BooleanField(default=False)
    assigned_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.support} assigned to Chat {self.chat.id}"
