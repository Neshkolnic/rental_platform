from django.urls import path
from . import views
from .views import (
    AdminLoginView,
    AdminDashboardView,
    ModerationListView,
    assign_moderator,
    approve_property,
    reject_property,
    SupportListView,
    assign_support,
    resolve_chat,
    MyAssignmentsView,
    AdminLoginView, AdminDashboardView, ModerationListView,
    assign_moderator, approve_property, reject_property,
    SupportListView, assign_support, resolve_chat,
    MyAssignmentsView, support_chat_detail
)

app_name = 'adminpanel'

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='login'),
    path('dashboard/', AdminDashboardView.as_view(), name='dashboard'),
    path('moderation/', ModerationListView.as_view(), name='moderation_list'),
    path('assign-moderator/<int:property_id>/', assign_moderator, name='assign_moderator'),
    path('approve/<int:assignment_id>/', approve_property, name='approve_property'),
    path('reject/<int:assignment_id>/', reject_property, name='reject_property'),
    path('support/', SupportListView.as_view(), name='support_list'),
    path('assign-support/<int:chat_id>/', assign_support, name='assign_support'),
    path('resolve-chat/<int:chat_id>/', resolve_chat, name='resolve_chat'),
    path('my-assignments/', MyAssignmentsView.as_view(), name='my_assignments'),
path('support/list/', views.SupportListView.as_view(), name='support_list'),
    path('support/assign/<int:chat_id>/', views.assign_support, name='assign_support'),
    path('my_assignments/', views.MyAssignmentsView.as_view(), name='my_assignments'),
    path('support/chat/<int:chat_id>/', support_chat_detail, name='support_chat_detail'),
path('support/chat/<int:chat_id>/', views.support_chat_detail, name='support_chat_detail'),
]
