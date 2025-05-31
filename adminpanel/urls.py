from django.urls import path
from . import views
from .views import MyAssignmentsView

app_name = 'adminpanel'

urlpatterns = [
    # Авторизация
    path('login/', views.AdminLoginView.as_view(), name='login'),

    # Главная панель
    path('dashboard/', views.AdminDashboardView.as_view(), name='dashboard'),

    # Модерация объявлений
    path('moderation/', views.ModerationListView.as_view(), name='moderation_list'),
    path('assign-moderator/<int:property_id>/', views.assign_moderator, name='assign_moderator'),
    path('approve/<int:assignment_id>/', views.approve_property, name='approve_property'),
    path('reject/<int:assignment_id>/', views.reject_property, name='reject_property'),

    # Поддержка
    path('support/', views.SupportListView.as_view(), name='support_list'),

    # Список необработанных чатов поддержки
    path('support/unassigned/', views.SupportUnassignedListView.as_view(), name='support_unassigned_chats'),


    # Назначить чат другому оператору (если нужно, можно убрать)
    path('support/assign/<int:chat_id>/', views.assign_support, name='assign_support'),
path('my-assignments/', MyAssignmentsView.as_view(), name='my_assignments'),
    # Назначить чат себе (отдельный URL, чтобы не конфликтовать)
    path('support/assign-self/<int:chat_id>/', views.assign_support_chat_to_self, name='assign_support_chat_to_self'),

    # Просмотр чата поддержки
    path('support/chat/<int:chat_id>/', views.support_chat_detail, name='support_chat_detail'),

    # Закрыть чат поддержки
    path('support/resolve/<int:chat_id>/', views.resolve_chat, name='resolve_chat'),

    # Мои задания
    # ... если есть другие урлы
]
