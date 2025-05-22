# chat/views.py

from django.shortcuts import render, get_object_or_404, redirect
from .models import Chat, Message
from booking.models import Booking
from django.contrib.auth.decorators import login_required
from django.db.models import Q



@login_required
def chat_room_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Находим чат, связанный с этим бронированием
    chat = Chat.objects.filter(booking=booking).first()

    # Если чат еще не создан, создаём его
    if not chat:
        chat = Chat.objects.create(
            booking=booking,
            tenant=booking.tenant,
            landlord=booking.property.owner
        )

    # Получаем все сообщения в этом чате
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