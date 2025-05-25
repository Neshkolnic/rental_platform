from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django import forms

from .models import ModerationAssignment, SupportAssignment
from booking.models import Property
from chat.models import Chat
from django.conf import settings
User = settings.AUTH_USER_MODEL
from django.contrib.auth.forms import AuthenticationForm


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


from chat.models import Chat
from adminpanel.models import SupportAssignment  # обязательно импортируй

class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'adminpanel/dashboard.html'

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_moderator or user.is_support)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from booking.models import Property
        context['unassigned_properties'] = Property.objects.filter(
            moderation_assignment__isnull=True,
            is_approved=False
        )

        if self.request.user.is_support:
            context['unassigned_chats'] = Chat.objects.filter(
                is_support_chat=True,
                support_assignment__isnull=True
            )

        return context

class ModerationListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'adminpanel/moderation_list.html'
    model = Property
    context_object_name = 'properties'

    def test_func(self):
        return self.request.user.is_moderator

    def get_queryset(self):
        # Только объявления без назначенного модератора и не утвержденные
        return Property.objects.filter(
            moderation_assignment__isnull=True,
            is_approved=False
        )


@login_required
def assign_moderator(request, property_id):
    if not request.user.is_moderator:
        return HttpResponseForbidden()

    property_obj = get_object_or_404(Property, id=property_id)

    # Не даём назначать, если уже есть модератор
    if ModerationAssignment.objects.filter(property=property_obj).exists():
        messages.error(request, "Это объявление уже назначено модератору.")
        return redirect('adminpanel:dashboard')

    assignment = ModerationAssignment.objects.create(property=property_obj, moderator=request.user)
    messages.success(request, "Объявление назначено вам для модерации.")
    return redirect('adminpanel:my_assignments')



@login_required
def approve_property(request, assignment_id):
    if not request.user.is_moderator:
        return HttpResponseForbidden()

    assignment = get_object_or_404(ModerationAssignment, id=assignment_id, moderator=request.user)
    assignment.is_approved = True
    assignment.save()

    # Отмечаем объявление как утвержденное
    property_obj = assignment.property
    property_obj.is_approved = True
    property_obj.save()

    messages.success(request, "Объявление успешно утверждено.")
    return redirect('adminpanel:my_assignments')


@login_required
def reject_property(request, assignment_id):
    if not request.user.is_moderator:
        return HttpResponseForbidden()

    assignment = get_object_or_404(ModerationAssignment, id=assignment_id, moderator=request.user)
    # Можно удалить объявление или отметить как отклоненное
    property_obj = assignment.property
    property_obj.is_approved = False
    property_obj.save()

    # Можно удалить назначение или оставить, чтобы показать как отклоненное
    assignment.delete()

    messages.success(request, "Объявление отклонено.")
    return redirect('adminpanel:my_assignments')


class SupportListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'adminpanel/support_list.html'
    model = Chat
    context_object_name = 'chats'

    def test_func(self):
        return self.request.user.is_support

    def get_queryset(self):
        # Чаты без саппорта
        return Chat.objects.filter(supportassignment__isnull=True)


@login_required
def assign_support(request, chat_id):
    if not request.user.is_support:
        return HttpResponseForbidden()

    chat_obj = get_object_or_404(Chat, id=chat_id)
    assignment, created = SupportAssignment.objects.get_or_create(chat=chat_obj)
    assignment.support = request.user
    assignment.save()
    messages.success(request, "Чат назначен вам.")

    # Перенаправляем к странице чата, чтобы менеджер сразу видел переписку
    return redirect('adminpanel:support_chat_detail', chat_id=chat_obj.id)

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Chat, SupportAssignment

@login_required
def support_chat_detail(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    # Проверяем, что это чат поддержки
    if not chat.is_support_chat:
        return HttpResponseForbidden("Это не чат поддержки.")

    user = request.user
    # Разрешаем доступ, если пользователь — саппорт или модератор (администратор)
    if not (user.is_support or user.is_moderator):
        return HttpResponseForbidden("У вас нет доступа к этому чату.")

    messages = chat.messages.all().order_by('created_at')

    # Обработка POST-запроса — отправка сообщений (если нужна)
    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            chat.messages.create(sender=user, content=content)
            return redirect('adminpanel:support_chat_detail', chat_id=chat.id)

    return render(request, 'adminpanel/support_chat_detail.html', {
        'chat': chat,
        'messages': messages,
    })



@login_required
def resolve_chat(request, chat_id):
    if not request.user.is_support:
        return HttpResponseForbidden()

    assignment = get_object_or_404(SupportAssignment, chat__id=chat_id, support=request.user)
    assignment.is_resolved = True
    assignment.save()

    messages.success(request, "Чат отмечен как решённый.")
    return redirect('adminpanel:my_assignments')



class MyAssignmentsView(LoginRequiredMixin, TemplateView):
    template_name = 'adminpanel/my_assignments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if hasattr(user, 'is_moderator') and user.is_moderator:
            context['my_properties'] = ModerationAssignment.objects.filter(moderator=user, is_approved=False)

        if hasattr(user, 'is_support') and user.is_support:
            context['my_chats'] = SupportAssignment.objects.filter(support=user, is_resolved=False)

        return context

@login_required
def chat_room_view(request, booking_id=None, chat_id=None):
    if chat_id:
        chat = get_object_or_404(Chat, id=chat_id)
    elif booking_id:
        booking = get_object_or_404(Booking, id=booking_id)
        chat = Chat.objects.filter(booking=booking).first()
        if not chat:
            chat = Chat.objects.create(
                booking=booking,
                tenant=booking.tenant,
                landlord=booking.property.owner
            )
    else:
        return HttpResponseForbidden("Чат не найден.")

    user = request.user

    if chat.is_support_chat:
        try:
            assignment = SupportAssignment.objects.get(chat=chat)
        except SupportAssignment.DoesNotExist:
            return HttpResponseForbidden("Доступ запрещён.")
        if assignment.support != user:
            return HttpResponseForbidden("Доступ запрещён.")
    else:
        if user != chat.tenant and user != chat.landlord:
            return HttpResponseForbidden("Доступ запрещён.")

    messages = chat.messages.all().order_by('created_at')

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            chat.messages.create(sender=user, content=message_text)

    return render(request, 'chat/chat_room.html', {
        'chat': chat,
        'messages': messages,
    })
