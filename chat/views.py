from django.shortcuts import render, get_object_or_404, redirect
from .models import Chat, Message
from booking.models import Booking
from django.contrib.auth.decorators import login_required
from django.db.models import Q


@login_required
def chat_room_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    chat = Chat.objects.filter(booking=booking).first()

    if not chat:
        chat = Chat.objects.create(
            booking=booking,
            tenant=booking.tenant,
            landlord=booking.property.owner
        )

    messages = chat.messages.all().order_by('created_at')

    return render(request, 'chat/chat_room.html', {
        'chat': chat,
        'messages': messages,
        'booking': booking,
    })


@login_required
def chat_list_view(request):
    user = request.user
    chats = Chat.objects.filter(Q(tenant=user) | Q(landlord=user)).select_related('booking__property')

    return render(request, 'chat/chat_list.html', {'chats': chats})


from adminpanel.models import SupportAssignment
from django.http import HttpResponseForbidden

@login_required
def support_chat_view(request):
    chat, created = Chat.objects.get_or_create(
        is_support_chat=True,
        tenant=request.user,
        defaults={'landlord': None, 'booking': None}
    )

    # Проверяем назначение саппорта, если оно есть
    try:
        assignment = SupportAssignment.objects.get(chat=chat)
        if assignment.support != request.user:
            return HttpResponseForbidden("У вас нет доступа к этому чату.")
    except SupportAssignment.DoesNotExist:
        # Нет назначенного саппорта — разрешаем пользователю писать в поддержку
        assignment = None

    if request.method == 'POST':
        content = request.POST.get('message', '').strip()
        if content:
            Message.objects.create(
                chat=chat,
                sender=request.user,
                content=content
            )
            return redirect('chat:support_chat')

    messages = chat.messages.all().order_by('created_at')
    return render(request, 'chat/chat_support.html', {
        'chat': chat,
        'messages': messages,
        'assignment': assignment,
    })
