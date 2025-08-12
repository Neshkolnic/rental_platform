from django.urls import path
from . import views
from .views import save_availability, api_availability_data, api_save_availability
from .views import leave_review_view
from django.http import HttpResponse
from django.contrib.auth import views as auth_views
from . import views
def payment_return_view(request):
    return HttpResponse("Payment Return")

def payment_success_view(request):
    return HttpResponse("Payment Success")

def payment_decline_view(request):
    return HttpResponse("Payment Decline")

def payment_fail_view(request):
    return HttpResponse("Payment Fail")

def payment_cancel_view(request):
    return HttpResponse("Payment Cancel")




urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('avatar/<int:user_id>/', views.avatar_view, name='avatar_view'),

    path('geocode/', views.geocode_view, name='geocode'),

    path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('calendar/edit/<int:property_id>/', views.calendar_edit, name='calendar_edit'),

    path('booking/<int:booking_id>/review/landlord/', views.leave_review_landlord_view, name='leave_review_landlord'),
    path('profile/', views.profile_view, name='profile'),
    # Отзыв собственника об арендаторе (tenant)
    path('booking/<int:booking_id>/review/tenant/', views.leave_review_tenant_view, name='leave_review_tenant'),

    # Отзыв арендатора об объекте (property)
    path('booking/<int:booking_id>/review/property/', views.leave_review_property_view, name='leave_review_property'),

    path('booking/<int:booking_id>/review/', leave_review_view, name='leave_review'),
    path('calendar/view/<int:property_id>/', views.calendar_view, name='calendar_view'),
    path('update-availability/<int:property_id>/<str:date_str>/', views.update_availability,
         name='update_availability'),

    # API availability paths — оставил только уникальные
    path('api/availability-data/', views.api_availability_data, name='api_availability_data'),
    # api_availability_data оставил, т.к. более полный и актуальный
    path('api/update-availability/', views.update_availability_ajax, name='update_availability_ajax'),
    path('api/save-availability/', views.api_save_availability, name='api_save_availability'),
    path('payment/start/', views.payment_start_view, name='payment_start'),
    path('payment/callback/', views.payment_callback_view, name='payment_callback'),  # для обработки результата оплаты
path('payment/return/', payment_return_view, name='payment_return'),
    path('payment/success/', payment_success_view, name='payment_success'),
    path('payment/decline/', payment_decline_view, name='payment_decline'),
    path('payment/fail/', payment_fail_view, name='payment_fail'),
    path('payment/cancel/', payment_cancel_view, name='payment_cancel'),
    path('password/code/', views.send_reset_code_view, name='send_reset_code'),
    path('password/code/verify/', views.verify_reset_code_view, name='verify_reset_code'),
    path('password/code/set/', views.set_new_password_view, name='set_new_password'),
    path('verify_email/', views.verify_email_view, name='verify_email'),
    path('verify_phone/', views.verify_phone_view, name='verify_phone'),
    path('resend-email-code/', views.resend_email_code_view, name='resend_email_code'),
    path('resend-phone-code/', views.resend_phone_code_view, name='resend_phone_code'),

]