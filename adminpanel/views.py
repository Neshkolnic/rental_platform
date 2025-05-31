from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.views.generic import TemplateView, ListView
from django.urls import reverse_lazy
from django.contrib import messages
from django import forms

from .models import ModerationAssignment, SupportAssignment
from booking.models import Property
from chat.models import Chat
from django.conf import settings

User = settings.AUTH_USER_MODEL


# ----------- АВТОРИЗАЦИЯ -------------
class AdminLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not (user.is_active and (user.is_moderator or user.is_support)):
            raise forms.ValidationError("Нет доступа к админской панели.", code='no_admin_access')


class AdminLoginView(LoginView):
    template_name = 'adminpanel/admin_login.html'
    authentication_form = AdminLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('adminpanel:dashboard')


# ----------- ДАШБОРД -------------
class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'adminpanel/dashboard.html'

    def test_func(self):
        return self.request.user.is_staff or getattr(self.request.user, 'is_support', False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Объявления без модератора (без ModerationAssignment)
        assigned_ids = ModerationAssignment.objects.values_list('property_id', flat=True)
        context['unassigned_properties'] = Property.objects.exclude(id__in=assigned_ids).filter(is_approved=False)

        if getattr(user, 'is_support', False):
            # Чаты поддержки без оператора (через отсутствие SupportAssignment)
            context['unassigned_chats'] = Chat.objects.filter(
                is_support_chat=True,
                support_assignment__isnull=True,   # Здесь: support_assignment, а не support_operator
                is_closed=False
            ).order_by('-created_at')

            # Активные чаты текущего оператора (через SupportAssignment.support)
            context['my_support_chats'] = Chat.objects.filter(
                is_support_chat=True,
                support_assignment__support=user,  # Здесь
                is_closed=False
            ).order_by('-updated_at')
        else:
            context['unassigned_chats'] = []
            context['my_support_chats'] = []

        return context


# ----------- МОДЕРАЦИЯ ОБЪЯВЛЕНИЙ -------------
class ModerationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'adminpanel/moderation_list.html'
    model = Property
    context_object_name = 'properties'

    def test_func(self):
        return self.request.user.is_moderator

    def get_queryset(self):
        return Property.objects.filter(
            moderation_assignment__isnull=True,
            is_approved=False
        )


@login_required
def assign_moderator(request, property_id):
    if not request.user.is_moderator:
        return HttpResponseForbidden()

    property_obj = get_object_or_404(Property, id=property_id)

    if ModerationAssignment.objects.filter(property=property_obj).exists():
        messages.error(request, "Это объявление уже назначено модератору.")
        return redirect('adminpanel:dashboard')

    ModerationAssignment.objects.create(property=property_obj, moderator=request.user)
    messages.success(request, "Объявление назначено вам для модерации.")
    return redirect('adminpanel:my_assignments')


@login_required
def approve_property(request, assignment_id):
    if not request.user.is_moderator:
        return HttpResponseForbidden()

    assignment = get_object_or_404(ModerationAssignment, id=assignment_id, moderator=request.user)
    assignment.is_approved = True
    assignment.save()

    property_obj = assignment.property
    property_obj.is_approved = True
    property_obj.save()

    messages.success(request, "Объявление утверждено.")
    return redirect('adminpanel:my_assignments')


@login_required
def reject_property(request, assignment_id):
    if not request.user.is_moderator:
        return HttpResponseForbidden()

    assignment = get_object_or_404(ModerationAssignment, id=assignment_id, moderator=request.user)
    assignment.delete()

    messages.success(request, "Объявление отклонено.")
    return redirect('adminpanel:my_assignments')


# ----------- ЧАТ ПОДДЕРЖКИ -------------
class SupportListView(LoginRequiredMixin, ListView):
    # убрал UserPassesTestMixin
    model = Chat
    template_name = 'adminpanel/support_list.html'
    context_object_name = 'chats'


    def test_func(self):
        return self.request.user.is_support


    def get_queryset(self):
        # Чаты поддержки без назначенного оператора
        return Chat.objects.filter(
            is_support_chat=True,
            is_closed=False,
            support_assignment__isnull=True  # Здесь исправлено
        ).order_by('-created_at')


@login_required
def assign_support(request, chat_id):
    if not request.user.is_support:
        return HttpResponseForbidden()

    chat_obj = get_object_or_404(Chat, id=chat_id)
    if chat_obj.is_closed:
        messages.error(request, "Чат уже закрыт.")
        return redirect('adminpanel:dashboard')

    # Создаём назначение оператора, если его нет
    assignment, created = SupportAssignment.objects.get_or_create(
        chat=chat_obj,
        defaults={'support': request.user}
    )

    if not created and assignment.support != request.user:
        messages.error(request, "Чат уже назначен другому оператору.")
        return redirect('adminpanel:dashboard')

    messages.success(request, "Чат назначен вам.")
    return redirect('adminpanel:support_chat_detail', chat_id=chat_obj.id)


@login_required
def support_chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)
    if not chat.is_support_chat:
        return HttpResponseForbidden("Это не чат поддержки.")

    user = request.user

    # Проверяем что пользователь является назначенным оператором
    assignment = getattr(chat, 'support_assignment', None)
    if not assignment or assignment.support != user:
        return HttpResponseForbidden("У вас нет доступа к этому чату.")

    messages_list = chat.messages.all().order_by('created_at')

    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            chat.messages.create(sender=user, content=content)
            return redirect('adminpanel:support_chat_detail', chat_id=chat.id)

    return render(request, 'adminpanel/support_chat_detail.html', {
        'chat': chat,
        'messages': messages_list,
    })


@login_required
def resolve_chat(request, chat_id):
    if not request.user.is_support:
        return HttpResponseForbidden()

    chat = get_object_or_404(Chat, id=chat_id)
    assignment = getattr(chat, 'support_assignment', None)

    if not assignment or assignment.support != request.user:
        return HttpResponseForbidden()

    chat.is_closed = True
    chat.save()

    assignment.is_resolved = True
    assignment.save()

    messages.success(request, "Чат закрыт.")
    return redirect('adminpanel:dashboard')


# ----------- МОИ НАЗНАЧЕНИЯ -------------
class MyAssignmentsView(LoginRequiredMixin, TemplateView):
    template_name = 'adminpanel/my_assignments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_moderator:
            context['my_properties'] = ModerationAssignment.objects.filter(
                moderator=user,
                is_approved=False
            )

        if user.is_support:
            context['my_chats'] = Chat.objects.filter(
                support_assignment__support=user,  # Здесь исправлено
                is_closed=False
            )

        return context


class SupportUnassignedListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Chat
    template_name = 'adminpanel/support_unassigned_list.html'
    context_object_name = 'chats'

    def test_func(self):
        return self.request.user.is_support

    def get_queryset(self):
        # Возвращаем только необработанные чаты поддержки без оператора
        return Chat.objects.filter(
            is_support_chat=True,
            support_assignment__isnull=True,  # Здесь
            is_closed=False
        ).order_by('-created_at')


@login_required
def assign_support_chat_to_self(request, chat_id):
    user = request.user
    # Разрешаем назначать чат и саппортам, и администраторам (staff)
    if not (user.is_support or user.is_staff):
        messages.error(request, "У вас нет прав для назначения чата.")
        return redirect('adminpanel:support_unassigned_chats')

    chat = get_object_or_404(Chat, id=chat_id, is_support_chat=True)

    if chat.is_closed:
        messages.error(request, "Чат уже закрыт.")
        return redirect('adminpanel:support_unassigned_chats')

    if hasattr(chat, 'support_assignment') and chat.support_assignment is not None:
        messages.error(request, "Чат уже назначен другому оператору.")
        return redirect('adminpanel:support_unassigned_chats')

    # Назначаем оператора через SupportAssignment
    SupportAssignment.objects.update_or_create(
        chat=chat,
        defaults={'support': user, 'is_resolved': False}
    )

    messages.success(request, f"Вы успешно назначили чат #{chat.id} себе.")
    return redirect('adminpanel:support_chat_detail', chat_id=chat.id)
