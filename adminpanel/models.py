from django.db import models
from booking.models import Property  # или твою модель объявления (если она называется иначе)
from django.conf import settings

User = settings.AUTH_USER_MODEL

class ModerationAssignment(models.Model):
    property = models.OneToOneField(Property, on_delete=models.CASCADE, related_name='moderation_assignment')
    moderator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_moderator': True}
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Assignment: {self.property.title} -> {self.moderator.username if self.moderator else 'unassigned'}"


from chat.models import Chat

class SupportAssignment(models.Model):
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE, related_name='support_assignment')
    support = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'is_support': True},
        related_name='adminpanel_support_assignments'  # уникальный related_name
    )
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Support: {self.chat.booking.id} -> {self.support.username if self.support else 'unassigned'}"
