from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView  # Добавьте этот импорт
from django.contrib.auth import views as auth_views
from booking.views import create_property, property_list
from booking import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('properties/create/', create_property, name='create_property'),
    path('properties/', property_list, name='property_list'),
    # Главная страница
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('my-properties/', views.my_properties, name='my_properties'),
    # URL приложения booking
    path('', include('booking.urls')),

    # URL allauth (социальная авторизация)
    path('accounts/', include('allauth.urls')),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]