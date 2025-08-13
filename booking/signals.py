from allauth.account.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

@receiver(user_logged_in)
def after_social_login(request, user, **kwargs):
    # Если это новый пользователь (через соцсеть) и не подтверждён телефон
    if not user.is_verified:
        return redirect('verify_phone_oauth')  # Переходим на страницу подтверждения телефона
    return redirect('/')  # Если всё ок — редиректим на главную
