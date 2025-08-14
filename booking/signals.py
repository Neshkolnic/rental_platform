# booking/signals.py

from django.dispatch import receiver
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount

User = get_user_model()

@receiver(pre_save, sender=User)
def unlink_social_on_email_change(sender, instance, **kwargs):
    try:
        old_user = User.objects.get(pk=instance.pk)
    except User.DoesNotExist:
        return  # Новый пользователь — не проверяем

    # Если email был изменён — отвязываем соц. аккаунты
    if old_user.email != instance.email:
        print("Email изменён. Удаляем соц. аккаунты...")
        SocialAccount.objects.filter(user=instance, provider__in=['google', 'yandex']).delete()
