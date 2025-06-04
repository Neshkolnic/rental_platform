from datetime import date, datetime, timedelta
import json
import os
from booking.tasks import schedule_review_reminder

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView

from geopy.geocoders import Nominatim

from .forms import UserRegisterForm, UserLoginForm, PropertyForm, AvailabilityCalendarForm
from .models import Property, PropertyPhoto, AvailabilityCalendar, Booking, User


def geocode_view(request):
    address = request.GET.get('address', '')
    geolocator = Nominatim(user_agent="property_app")
    try:
        location = geolocator.geocode(address)
        if location:
            return JsonResponse({'lat': location.latitude, 'lon': location.longitude})
    except Exception:
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
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                property_obj = form.save(owner=request.user)
                messages.success(request, 'Объект и фотографии успешно сохранены!')
                return redirect('property_detail', pk=property_obj.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при сохранении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PropertyForm()
    return render(request, 'property/create.html', {'form': form})


def property_list(request):
    properties = Property.objects.filter(is_active=True)
    for prop in properties:
        prop.first_photo = prop.photos.first()
        prop.short_description = prop.description[:100]
    return render(request, 'property/list.html', {'properties': properties})


def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    bookings = Booking.objects.filter(property=property_obj)

    booked_dates = []
    for booking in bookings:
        current_date = booking.check_in_date
        while current_date < booking.check_out_date:
            booked_dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)

    return render(request, 'property/detail.html', {
        'property': property_obj,
        'booked_dates': json.dumps(booked_dates),
    })


@login_required
def my_properties(request):
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'property/my_properties.html', {'properties': properties})


class PropertyCreateView(CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property/create.html'
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


@login_required
def booking_confirm_view(request, property_id):
    property_obj = get_object_or_404(Property, pk=property_id)

    check_in = request.GET.get('check_in')
    check_out = request.GET.get('check_out')

    if not check_in or not check_out:
        return render(request, 'error.html', {'message': 'Пожалуйста, выберите обе даты.'})

    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
    except ValueError:
        return render(request, 'error.html', {'message': 'Некорректный формат дат.'})

    if check_out_date <= check_in_date:
        return render(request, 'error.html', {'message': 'Дата выезда должна быть позже даты заезда.'})

    total_days = (check_out_date - check_in_date).days
    if total_days <= 0:
        return render(request, 'error.html', {'message': 'Продолжительность бронирования должна быть хотя бы 1 день.'})

    total_price = total_days * property_obj.price_per_night

    if request.method == 'POST':
        booking = Booking.objects.create(
            tenant=request.user,
            property=property_obj,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            total_price=total_price,
            status=Booking.Status.PENDING
        )
        schedule_review_reminder.apply_async(args=[booking.id], countdown=3)
        return redirect('chat:chat_room', booking_id=booking.id)

    return render(request, 'booking/confirm.html', {
        'property': property_obj,
        'check_in': check_in,
        'check_out': check_out,
        'total_price': total_price,
    })


@login_required
def property_edit(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)

    if request.method == 'POST':
        property_obj.title = request.POST.get('title')
        property_obj.description = request.POST.get('description')
        property_obj.price_per_night = request.POST.get('price_per_night')
        property_obj.save()
        return redirect('property_edit', pk=property_obj.pk)

    return render(request, 'property/property_edit.html', {'property': property_obj})


@login_required
def calendar_edit(request, property_id):
    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)
    return render(request, 'property/calendar_edit.html', {'property': property_obj})



@login_required
def update_availability(request, property_id, date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
    availability = AvailabilityCalendar.objects.get(property_id=property_id, date=date_obj)

    if request.method == 'POST':
        form = AvailabilityCalendarForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            return redirect('calendar_edit')
        else:
            return render(request, 'property/calendar_edit.html', {'form': form, 'error': 'Form is not valid.'})

    return render(request, 'property/update_availability.html', {'availability': availability})


@login_required
def calendar_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    availability_calendar = AvailabilityCalendar.objects.filter(property=property_obj)

    return render(request, 'property/calendar_view.html', {
        'property': property_obj,
        'availability_calendar': availability_calendar
    })


@require_GET
def availability_data(request):
    property_id = request.GET.get('property_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not (property_id and start_date_str and end_date_str):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        property_obj = Property.objects.get(pk=property_id)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except (Property.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    days_count = (end_date - start_date).days
    if days_count <= 0:
        return JsonResponse({'error': 'Invalid date range'}, status=400)

    availability_records = AvailabilityCalendar.objects.filter(
        property=property_obj,
        date__gte=start_date,
        date__lt=end_date
    ).order_by('date')

    result = []
    unavailable = False
    total_price = 0
    current_date = start_date

    for _ in range(days_count):
        record = next((r for r in availability_records if r.date == current_date), None)

        if record:
            is_available = record.is_available
            price = record.price if record.price is not None else property_obj.price_per_night
        else:
            is_available = True
            price = property_obj.price_per_night

        if not is_available:
            unavailable = True

        total_price += float(price)
        result.append({
            'date': current_date.isoformat(),
            'is_available': is_available,
            'price': float(price)
        })
        current_date += timedelta(days=1)

    return JsonResponse({
        'dates': result,
        'total_price': total_price,
        'is_available': not unavailable,
    })


@csrf_exempt  # временно, потом заменить на проверку токена/CSRF
@require_POST
@login_required
def update_availability_ajax(request):
    try:
        data = json.loads(request.body)
        property_id = data['property_id']
        date_str = data['date']
        is_available = data['is_available']
        price = data.get('price', '')

        date_obj = date.fromisoformat(date_str)
        prop = Property.objects.get(id=property_id, owner=request.user)

        obj, _ = AvailabilityCalendar.objects.get_or_create(property=prop, date=date_obj)
        obj.is_available = is_available
        obj.price = price if price != '' else None
        obj.save()

        return JsonResponse({'status': 'ok'})
    except Property.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Property not found or not owned by user'}, status=403)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def save_availability(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        property_id = data.get('property_id')
        date_str = data.get('date')
        price = data.get('price')
        is_available = data.get('is_available')

        if not all([property_id, date_str, price is not None, is_available is not None]):
            return JsonResponse({'error': 'Missing data'}, status=400)

        property_obj = Property.objects.get(pk=property_id)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        record, created = AvailabilityCalendar.objects.get_or_create(property=property_obj, date=date_obj)
        record.price = price
        record.is_available = is_available
        record.save()

        return JsonResponse({'success': True})
    except Exception:
        return JsonResponse({'error': 'Invalid data'}, status=400)


@require_GET
def api_availability_data(request):
    property_id = request.GET.get('property_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    try:
        property_obj = Property.objects.get(pk=property_id)
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except Exception:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    days = (end_date - start_date).days
    if days <= 0:
        return JsonResponse({'error': 'Invalid date range'}, status=400)

    availability_records = AvailabilityCalendar.objects.filter(
        property=property_obj,
        date__gte=start_date,
        date__lt=end_date
    ).order_by('date')

    data = {}
    for rec in availability_records:
        data[rec.date.isoformat()] = {
            'price': float(rec.price) if rec.price is not None else float(property_obj.price_per_night),
            'is_available': rec.is_available
        }

    result = []
    current = start_date
    while current < end_date:
        day_str = current.isoformat()
        if day_str not in data:
            data[day_str] = {
                'price': float(property_obj.price_per_night),
                'is_available': True
            }
        result.append({
            'date': day_str,
            'price': data[day_str]['price'],
            'is_available': data[day_str]['is_available']
        })
        current += timedelta(days=1)

    return JsonResponse({'dates': result})


@csrf_exempt
def api_save_availability(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)

    try:
        data = json.loads(request.body)
        property_id = data['property_id']
        date_str = data['date']
        price = data['price']
        is_available = data['is_available']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    try:
        property_obj = Property.objects.get(pk=property_id)
        date_obj = date.fromisoformat(date_str)
    except Exception:
        return JsonResponse({'error': 'Invalid property or date'}, status=400)

    record, _ = AvailabilityCalendar.objects.get_or_create(property=property_obj, date=date_obj)
    record.price = price
    record.is_available = is_available
    record.save()

    return JsonResponse({'success': True})


from .models import Booking, Review
from .forms import ReviewForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


@login_required
def leave_review_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)

    if hasattr(booking, 'review'):
        return HttpResponse("Вы уже оставили отзыв.")

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.property = booking.property
            review.author = request.user
            review.save()
            return redirect('property_detail', pk=booking.property.id)
    else:
        form = ReviewForm()

    return render(request, 'reviews/leave_review.html', {'form': form, 'booking': booking})



from .forms import ProfileForm

@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile_view')
    else:
        form = ProfileForm(instance=user)

    # Получаем все отзывы пользователя
    reviews = user.get_all_reviews()

    return render(request, 'profile/profile.html', {
        'form': form,
        'reviews': reviews,
    })



@login_required
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('profile_view')
    else:
        form = ProfileForm(instance=user)

    reviews = user.get_all_reviews()

    return render(request, 'profile/profile.html', {
        'form': form,
        'reviews': reviews,
    })


# ➕ Добавим avatar_view

def avatar_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.avatar:
        return HttpResponse(user.avatar, content_type='image/jpeg')  # или 'image/png'
    raise Http404("Avatar not found")

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from .models import Booking, Review, Property

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Booking, Review
from .forms import ReviewForm

@login_required
def leave_review_landlord_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Проверяем, что текущий пользователь — арендатор брони
    if request.user != booking.tenant:
        return HttpResponse("У вас нет прав оставлять отзыв об этом владельце.", status=403)

    # Если отзыв уже есть, можно не позволять оставить ещё один (по желанию)
    if Review.objects.filter(booking=booking, review_type='landlord').exists():
        return HttpResponse("Вы уже оставили отзыв об этом владельце.")

    if request.method == 'POST':
        # Если используешь форму:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.property = booking.property
            review.author = request.user
            review.to_user = booking.property.owner
            review.review_type = 'landlord'
            review.save()
            return redirect('profile_view')

        # Если формы нет — ниже пример с ручной обработкой:
        # rating = request.POST.get('rating')
        # if not rating:
        #     return render(request, 'booking/leave_review_landlord.html', {
        #         'booking': booking,
        #         'error': 'Пожалуйста, укажите рейтинг.'
        #     })
        # try:
        #     rating = int(rating)
        # except ValueError:
        #     return render(request, 'booking/leave_review_landlord.html', {
        #         'booking': booking,
        #         'error': 'Некорректный рейтинг.'
        #     })
        # comment = request.POST.get('comment', '')
        # Review.objects.create(
        #     booking=booking,
        #     review_type='landlord',
        #     author=request.user,
        #     to_user=booking.property.owner,
        #     property=booking.property,
        #     rating=rating,
        #     comment=comment
        # )
        # return redirect('profile_view')

    else:
        form = ReviewForm()

    return render(request, 'booking/leave_review_landlord.html', {
        'booking': booking,
        'form': form,
    })

@login_required
def leave_review_tenant_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.property.owner:
        return HttpResponse("У вас нет прав оставлять отзыв об этом жильце.", status=403)

    if Review.objects.filter(booking=booking, review_type='tenant').exists():
        return HttpResponse("Вы уже оставили отзыв об этом жильце.")

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.property = booking.property
            review.author = request.user
            review.to_user = booking.tenant
            review.review_type = 'tenant'
            review.save()
            return redirect('profile_view')
    else:
        form = ReviewForm()

    return render(request, 'booking/leave_review_tenant.html', {
        'booking': booking,
        'form': form,
    })

@login_required
def leave_review_property_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if request.user != booking.tenant:
        return HttpResponse("У вас нет прав оставлять отзыв об этом объекте.", status=403)

    if Review.objects.filter(booking=booking, review_type='property').exists():
        return HttpResponse("Вы уже оставили отзыв об этом объекте.")

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.booking = booking
            review.property = booking.property
            review.author = request.user
            review.to_user = None
            review.review_type = 'property'
            review.save()
            return redirect('profile_view')
    else:
        form = ReviewForm()

    return render(request, 'booking/leave_review_property.html', {
        'booking': booking,
        'form': form,
    })
