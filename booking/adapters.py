from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse
from allauth.exceptions import ImmediateHttpResponse

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        # Если пользователь уже существует, ничего не делаем
        if sociallogin.is_existing:
            return

        # Если пользователь новый — сохраняем данные соцсети в сессии и редиректим на подтверждение телефона
        request.session['socialaccount_sociallogin'] = sociallogin.serialize()
        raise ImmediateHttpResponse(redirect(reverse('phone_verification_start')))
