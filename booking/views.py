from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm, UserLoginForm, PropertyForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from geopy.geocoders import Nominatim
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Property, PropertyPhoto
from django.contrib import messages
from .models import AvailabilityCalendar
from datetime import date
from datetime import timedelta
import json

import os
from django.conf import settings


def geocode_view(request):
    address = request.GET.get('address', '')
    geolocator = Nominatim(user_agent="property_app")
    try:
        location = geolocator.geocode(address)
        if location:
            return JsonResponse({'lat': location.latitude, 'lon': location.longitude})
    except:
        pass
    return JsonResponse({'error': 'Адрес не найден'}, status=400)


def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def create_property(request):
    if request.method == 'POST':
        print(f"Получено файлов в request.FILES: {len(request.FILES.getlist('photos'))}")
        form = PropertyForm(request.POST, request.FILES)

        if form.is_valid():
            print(f"Валидные данные, фотографий в cleaned_data: {len(form.cleaned_data.get('photos', []))}")
            try:
                property_obj = form.save(owner=request.user)
                messages.success(request, 'Объект и фотографии успешно сохранены!')
                return redirect('property_detail', pk=property_obj.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
                print(f"Ошибка сохранения: {str(e)}")
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
            print("Ошибки формы:", form.errors)
    else:
        form = PropertyForm()

    return render(request, 'property/create.html', {'form': form})


def property_list(request):
    properties = Property.objects.filter(is_active=True)
    for property in properties:
        # Получаем первую фотографию
        property.first_photo = property.photos.first()
        property.short_description = property.description[:100]
    return render(request, 'property/list.html', {'properties': properties})

from django.shortcuts import get_object_or_404
def property_detail(request, pk):
    property = get_object_or_404(Property, pk=pk)
    bookings = Booking.objects.filter(property=property)

    # Собираем занятые даты (от check_in до check_out НЕ включительно)
    booked_dates = []
    for booking in bookings:
        current_date = booking.check_in_date
        while current_date < booking.check_out_date:
            booked_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    return render(request, 'property/detail.html', {
        'property': property,
        'booked_dates': json.dumps(booked_dates),  # ← передаем в шаблон
    })

@login_required
def my_properties(request):
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'property/my_properties.html', {'properties': properties})


class PropertyCreateView(CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property/create.html'  # Путь к вашему шаблону
    success_url = reverse_lazy('property_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        files = self.request.FILES.getlist('photos')
        for i, photo in enumerate(files):
            PropertyPhoto.objects.create(
                property=self.object,
                image=photo,
                is_primary=(i == 0),
                order_index=i
            )
        return response

from django.contrib.auth.decorators import login_required
from .models import Booking

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date
from .models import Property, Booking


@login_required
def booking_confirm_view(request, property_id):
    # Получаем объект недвижимости
    property = get_object_or_404(Property, pk=property_id)

    # Получаем параметры check_in и check_out из GET-запроса
    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    # Проверяем, что обе даты переданы
    if not check_in or not check_out:
        return render(request, 'error.html', {'message': 'Пожалуйста, выберите обе даты.'})

    # Преобразуем строки в объекты даты
    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
    except ValueError:
        return render(request, 'error.html', {'message': 'Некорректный формат дат.'})

    # Проверка, что дата выезда не раньше даты заезда
    if check_out_date <= check_in_date:
        return render(request, 'error.html', {'message': 'Дата выезда должна быть позже даты заезда.'})

    # Вычисляем количество дней
    total_days = (check_out_date - check_in_date).days
    total_price = total_days * property.price_per_night

    if total_days <= 0:
        return render(request, 'error.html', {'message': 'Продолжительность бронирования должна быть хотя бы 1 день.'})

    # Если POST-запрос, создаем бронирование
    if request.method == 'POST':
        booking = Booking.objects.create(
            tenant=request.user,
            property=property,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_price=total_price,
            status=Booking.Status.PENDING
        )
        # Перенаправляем в чат
        return redirect('chat_room', booking_id=booking.id)

    # Возвращаем страницу подтверждения бронирования с данными
    return render(request, 'booking/confirm.html', {
        'property': property,
        'check_in': check_in,
        'check_out': check_out,
        'total_price': total_price,
    })

from django.shortcuts import render, get_object_or_404, redirect
from .models import Property, AvailabilityCalendar
from .forms import AvailabilityCalendarForm
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from .forms import PropertyForm
from .models import Property
from django.contrib.auth.decorators import login_required

from .forms import AvailabilityCalendarForm


@login_required
def property_edit(request, pk):
    property = get_object_or_404(Property, pk=pk)

    if request.method == 'POST':
        # Обработка формы редактирования объявления
        title = request.POST.get('title')
        description = request.POST.get('description')
        price_per_night = request.POST.get('price_per_night')

        property.title = title
        property.description = description
        property.price_per_night = price_per_night
        property.save()

        return redirect('property_edit', pk=property.pk)

    return render(request, 'property/property_edit.html', {'property': property})


@login_required
def calendar_edit(request):
    # Получаем все объявления текущего пользователя
    user_properties = Property.objects.filter(owner=request.user)

    return render(request, 'property/calendar_edit.html', {'user_properties': user_properties})


@login_required
def update_availability(request, property_id, date_str):
    # Обновляем доступность и цену для конкретного дня
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    availability = AvailabilityCalendar.objects.get(property_id=property_id, date=date)

    if request.method == 'POST':
        form = AvailabilityCalendarForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            return redirect('calendar_edit')
        else:
            return render(request, 'property/calendar_edit.html', {'form': form, 'error': 'Form is not valid.'})

    return render(request, 'property/update_availability.html', {'availability': availability})

# booking/views.py
@login_required
def calendar_view(request, property_id):
    property = get_object_or_404(Property, id=property_id)
    availability_calendar = AvailabilityCalendar.objects.filter(property=property)

    return render(request, 'property/calendar_view.html', {
        'property': property,
        'availability_calendar': availability_calendar
    })