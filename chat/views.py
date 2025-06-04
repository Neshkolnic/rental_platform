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
    chat, _ = Chat.objects.get_or_create(
        is_support_chat=True,
        tenant=request.user,
        defaults={'booking': None, 'landlord': None}
    )

    messages = chat.messages.all().order_by('created_at')

    return render(request, 'chat/chat_support.html', {
        'chat': chat,
        'messages': messages,
    })
