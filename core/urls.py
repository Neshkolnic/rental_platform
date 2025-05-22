from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView  # Добавьте этот импорт
from django.contrib.auth import views as auth_views
from booking.views import create_property, property_list
from booking import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('properties/create/', create_property, name='create_property'),
    path('booking/<int:property_id>/confirm/', views.booking_confirm_view, name='booking_confirm'),
    path('properties/', property_list, name='property_list'),
    path('properties/<int:pk>/', views.property_detail, name='property_detail'),
    # Главная страница
    path('chat/', include('chat.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('my-properties/', views.my_properties, name='my_properties'),
    # URL приложения booking
    path('', include('booking.urls')),
     path('properties/create/', create_property, name='create_property'),
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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

