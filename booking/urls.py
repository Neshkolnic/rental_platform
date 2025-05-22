from django.urls import path
from . import views
from .views import property_edit

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('geocode/', views.geocode_view, name='geocode'),
path('property/<int:pk>/edit/', views.property_edit, name='property_edit'),
    path('calendar/edit/', views.calendar_edit, name='calendar_edit'),
    path('calendar/view/<int:property_id>/', views.calendar_view, name='calendar_view'),
    path('update-availability/<int:property_id>/<str:date_str>/', views.update_availability, name='update_availability'),


]