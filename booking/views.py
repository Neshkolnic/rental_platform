from datetime import date, datetime, timedelta
import json
import os
from django.contrib.auth.forms import PasswordResetForm
from booking.tasks import schedule_review_reminder
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django import forms
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
from .models import Property, PropertyPhoto, AvailabilityCalendar, Booking, User, Message



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


from django.shortcuts import render, redirect
from django.contrib.auth import login
from booking.models import User

from .forms import UserRegisterForm

from django.core.mail import send_mail
import random
import string



from django.core.mail import send_mail
from django.contrib.auth import login
from django.shortcuts import render, redirect
from .forms import UserRegisterForm


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from .models import User

from django.contrib import messages
from django.shortcuts import render, redirect
from .models import EmailVerificationCode, PhoneVerificationCode
from .utils import send_sms  # твоя функция отправки SMS
from django.core.mail import send_mail

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            messages.error(request, 'Пароли не совпадают')
            return render(request, 'registration/register.html')

        # Проверка email и телефона на существование и валидность опущена для краткости

        # Сохраняем данные в сессии для дальнейшей регистрации
        request.session['register_email'] = email
        request.session['register_phone'] = phone
        request.session['register_password'] = password  # Лучше зашифровать или сохранить хэш

        # Генерируем и отправляем код на email
        email_code = generate_code()
        EmailVerificationCode.objects.create(email=email, code=email_code)
        send_mail(
            'Ваш код подтверждения email',
            f'Ваш код: {email_code}',
            'no-reply@example.com',
            [email],
        )



        messages.success(request, 'Код отправлен на email. Подтвердите его.')
        return redirect('verify_email')

    return render(request, 'registration/register.html')

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверные данные. Можете сбросить пароль.')

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


from .forms import InitialMessageForm  # Импортируем новую форму

from django.shortcuts import redirect
from django.urls import reverse

from decimal import Decimal
from datetime import date
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

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

    # Предполагается, что property_obj.price_per_night — Decimal или float
    # Если float — конвертируем в Decimal для точности вычислений
    price_per_night = property_obj.price_per_night
    if not isinstance(price_per_night, Decimal):
        price_per_night = Decimal(str(price_per_night))

    total_price = Decimal(total_days) * price_per_night
    deposit = total_price * Decimal('0.10')  # 10% предоплата

    if request.method == 'POST':
        form = InitialMessageForm(request.POST)
        if form.is_valid():
            booking = Booking.objects.create(
                tenant=request.user,
                property=property_obj,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                total_price=total_price,
                deposit_paid=False,  # Пока предоплата не оплачена
                status=Booking.Status.PENDING
            )

            from .utils import send_telegram_notification

            if property_obj.owner.telegram_id:
                send_telegram_notification(
                    telegram_id=property_obj.owner.telegram_id,
                    message=f"Новая бронь от {request.user.username} на даты {check_in} - {check_out}. Ожидается оплата предоплаты."
                )

            Message.objects.create(
                sender=request.user,
                receiver=property_obj.owner,
                booking=booking,
                text=form.cleaned_data['message']
            )

            # Сохраняем ID брони в сессии для оплаты
            request.session['booking_id'] = booking.id

            # Перенаправляем на страницу оплаты
            return redirect(reverse('payment_start'))

    else:
        form = InitialMessageForm()

    return render(request, 'booking/confirm.html', {
        'property': property_obj,
        'check_in': check_in,
        'check_out': check_out,
        'total_price': total_price,
        'deposit': deposit,
        'form': form
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

import base64
import requests
import json
from decimal import Decimal

from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Booking  # Импортируй свои модели


BEPAID_API_URL = 'https://checkout.bepaid.by/ctp/api/checkouts'
BEPAID_MERCHANT_ID = '363'
BEPAID_SECRET_KEY = '63b6faa98cc31cf70c9b764a3b9bbd423def29ecadff935cf4cce49665d8ed8f'


def get_bepaid_auth_header():
    auth_str = f"{BEPAID_MERCHANT_ID}:{BEPAID_SECRET_KEY}"
    auth_bytes = auth_str.encode('utf-8')
    encoded_auth = base64.b64encode(auth_bytes).decode('utf-8')
    return f"Basic {encoded_auth}"


@login_required
def payment_start_view(request):
    booking_id = request.GET.get('booking_id') or request.session.get('booking_id')
    if not booking_id:
        return HttpResponse("Ошибка: не найдено бронирование в сессии.", status=400)

    booking = get_object_or_404(Booking, id=booking_id, tenant=request.user)

    try:
        # 10% предоплаты, переводим в копейки
        amount_cents = int((booking.total_price * Decimal('0.10') * 100).quantize(Decimal('1')))
    except Exception as e:
        return HttpResponse(f"Ошибка при вычислении суммы: {e}", status=500)

    payload = {
        "checkout": {
            "test": True,
            "transaction_type": "payment",
            "attempts": 3,
            "settings": {
                "return_url": request.build_absolute_uri(
    reverse('payment_return') + f"?booking_id={booking.id}"),
                "success_url": request.build_absolute_uri(reverse('payment_success')),
                "decline_url": request.build_absolute_uri(reverse('payment_decline')),
                "fail_url": request.build_absolute_uri(reverse('payment_fail')),
                "cancel_url": request.build_absolute_uri(reverse('payment_cancel')),
                "notification_url": request.build_absolute_uri(reverse('payment_callback')),
                "button_next_text": "Вернуться в магазин",
                "language": "ru"
            },
            "payment_method": {
                "types": ["credit_card"]  # УДАЛИЛИ "bank_card"
            },
            "order": {
                "currency": "BYN",
                "amount": amount_cents,
                "description": f"Предоплата за бронирование №{booking.id}"
            },
            "customer": {
                "email": request.user.email,
            }
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': get_bepaid_auth_header(),
    }

    try:
        response = requests.post(BEPAID_API_URL, headers=headers, json=payload)
    except Exception as e:
        return HttpResponse(f"Ошибка при отправке запроса: {e}", status=500)

    if response.status_code not in (200, 201):
        return HttpResponse(f"Ошибка создания платежа: {response.status_code} {response.text}", status=500)

    try:
        resp_data = response.json()
    except Exception as e:
        return HttpResponse(f"Ошибка при разборе ответа: {e}", status=500)

    payment_url = resp_data.get('checkout', {}).get('redirect_url') or resp_data.get('checkout', {}).get('url')
    if not payment_url:
        return HttpResponse("Ошибка получения ссылки на оплату.", status=500)

    return redirect(payment_url)


@csrf_exempt
def payment_callback_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)



    shop_order_id = data.get('order', {}).get('shop_order_id') or data.get('shop_order_id')
    status = data.get('status')

    if not shop_order_id or not status:
        return JsonResponse({'error': 'Missing fields'}, status=400)

    try:
        booking = Booking.objects.get(id=shop_order_id)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)

    if status == 'paid':
        booking.deposit_paid = True
        booking.save()

    return JsonResponse({'status': 'ok'})
import json
import hmac
import hashlib

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Booking


BEPAID_SECRET_KEY = '63b6faa98cc31cf70c9b764a3b9bbd423def29ecadff935cf4cce49665d8ed8f'


@csrf_exempt
def payment_callback_view(request):
    try:
        raw_body = request.body
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # ✅ [Опционально] Проверка подписи (если Bepaid шлёт HMAC в заголовке X-Signature)
    received_signature = request.headers.get('X-Signature')
    if received_signature:
        calculated_signature = hmac.new(
            key=BEPAID_SECRET_KEY.encode('utf-8'),
            msg=raw_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        if calculated_signature != received_signature:
            return JsonResponse({'error': 'Invalid signature'}, status=403)

    # 🔍 Получаем ID заказа и статус
    shop_order_id = (
        data.get('order', {}).get('shop_order_id') or
        data.get('checkout', {}).get('order', {}).get('shop_order_id')
    )
    status = data.get('transaction', {}).get('status') or data.get('status')

    if not shop_order_id or not status:
        return JsonResponse({'error': 'Missing fields'}, status=400)

    try:
        booking = Booking.objects.get(id=shop_order_id)
    except Booking.DoesNotExist:
        return JsonResponse({'error': 'Booking not found'}, status=404)

    if status == 'successful' or status == 'paid':
        booking.deposit_paid = True
        booking.save()

    return JsonResponse({'status': 'ok'})


from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Booking

# @login_required
# def payment_return_view(request):
#     status = request.GET.get('status')
#     token = request.GET.get('token')
#     uid = request.GET.get('uid')
#
#     # Попытка получить booking_id из сессии
#     booking_id = request.session.get('booking_id')
#
#     if not booking_id:
#         # Если booking_id не в сессии, можно попытаться получить из параметров URL, если есть
#         booking_id = request.GET.get('booking_id')
#
#     if not booking_id:
#         # fallback — например, редирект на профиль
#         return redirect('profile_view')
#
#     booking = get_object_or_404(Booking, id=booking_id)
#
#     # Проверяем права пользователя
#     if request.user != booking.tenant and request.user != booking.property.owner:
#         return redirect('profile_view')
#
#     # Проверяем статус оплаты, который пришёл в URL (лучше полагаться на вебхук, но если надо)
#     if status != 'successful' and not booking.deposit_paid:
#         # Если оплата не прошла, редирект куда нужно
#         return redirect('profile_view')
#
#     # Тут можно сохранить token и uid в booking или логах, если нужно
#
#     # Перенаправляем в чат
#     return redirect('chat:chat_room', booking_id=booking.id)

@login_required
def payment_return_view(request):
    status = request.GET.get('status')
    booking_id = request.GET.get('booking_id') or request.session.get('booking_id')

    if not booking_id:
        # Если booking_id нет — редирект на профиль или другую страницу
        return redirect('profile_view')

    booking = get_object_or_404(Booking, id=booking_id)

    # Проверяем, что текущий пользователь — арендатор или владелец бронирования
    if request.user != booking.tenant and request.user != booking.property.owner:
        return redirect('profile_view')

    # Проверяем статус оплаты
    # Если в GET есть статус и он успешный — считаем оплату успешной
    # Или если уже в базе указано, что депозит оплачен
    if status != 'successful' and not booking.deposit_paid:
        # Оплата не прошла — редирект куда нужно
        return redirect('profile_view')

    # Все проверки пройдены — редиректим в чат с booking_id
    return redirect('chat:chat_room', booking_id=booking.id)

from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from .models import PasswordResetCode
from django.shortcuts import get_object_or_404

from django.contrib import messages  # не забудь импортировать

def send_reset_code_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Пользователь с таким email не найден')
            return render(request, 'registration/send_reset_code.html')

        # Удаляем старые коды
        PasswordResetCode.objects.filter(user=user).delete()

        # Генерация нового кода
        code = get_random_string(length=6, allowed_chars='0123456789')

        # Сохраняем код
        PasswordResetCode.objects.create(user=user, code=code)

        # Отправляем на почту
        send_mail(
            'Код для сброса пароля',
            f'Ваш код для сброса пароля: {code}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        request.session['reset_email'] = email
        return redirect('verify_reset_code')

    return render(request, 'registration/send_reset_code.html')




def verify_reset_code_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('send_reset_code')

    user = get_object_or_404(User, email=email)

    if request.method == 'POST':
        code_input = request.POST.get('code')

        # Получаем последний код
        reset_code = PasswordResetCode.objects.filter(user=user).order_by('-created_at').first()

        if not reset_code or reset_code.code != code_input:
            messages.error(request, 'Неверный код')
        elif reset_code.is_expired():
            messages.error(request, 'Код истёк')
        else:
            request.session['verified_user_id'] = user.id
            return redirect('set_new_password')

    return render(request, 'registration/verify_reset_code.html')


from django.contrib.auth.hashers import make_password

def set_new_password_view(request):
    user_id = request.session.get('verified_user_id')
    if not user_id:
        return redirect('send_reset_code')

    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
        elif len(password1) < 6:
            messages.error(request, 'Пароль должен быть не менее 6 символов')
        else:
            user.password = make_password(password1)
            user.save()

            # Чистим сессию
            request.session.flush()
            messages.success(request, 'Пароль успешно обновлён. Войдите в систему.')
            return redirect('login')

    return render(request, 'registration/set_new_password.html')




from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User
from django.utils import timezone

from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import EmailVerificationCode

def verify_email_view(request):
    email = request.session.get('register_email')
    phone = request.session.get('register_phone')  # <-- нужен для отправки SMS
    if not email:
        messages.error(request, 'Сначала введите email для регистрации.')
        return redirect('register')

    verification_record = EmailVerificationCode.objects.filter(email=email).order_by('-created_at').first()
    if not verification_record:
        messages.error(request, 'Код для подтверждения не был отправлен.')
        return redirect('register')

    if request.method == 'POST':
        code = request.POST.get('code')

        if verification_record.code != code:
            messages.error(request, 'Неверный код. Попробуйте снова.')
        elif verification_record.is_expired():
            messages.error(request, 'Срок действия кода истёк. Запросите новый код.')
        else:
            request.session['email_verified'] = True
            messages.success(request, 'Email подтверждён!')

            # ➕ Отправляем код на телефон только после подтверждения email
            phone_code = generate_code()
            PhoneVerificationCode.objects.create(phone=phone, code=phone_code)
            send_sms(phone, f'Ваш код подтверждения: {phone_code}')

            return redirect('verify_phone')

    return render(request, 'registration/verify_email.html')

from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import PhoneVerificationCode

def verify_phone_view(request):
    phone = request.session.get('register_phone')
    if not phone:
        messages.error(request, 'Сначала введите телефон для регистрации.')
        return redirect('register')

    verification_record = PhoneVerificationCode.objects.filter(phone=phone).order_by('-created_at').first()
    if not verification_record:
        messages.error(request, 'Код для подтверждения не был отправлен.')
        return redirect('register')

    if request.method == 'POST':
        code = request.POST.get('code')


        if verification_record.code != code:
            messages.error(request, 'Неверный код. Попробуйте снова.')
        elif verification_record.is_expired():
            messages.error(request, 'Срок действия кода истёк. Запросите новый код.')
        else:
            request.session['phone_verified'] = True
            messages.success(request, 'Телефон подтверждён!')

            # Теперь создаём пользователя, только если оба подтверждения пройдены
            if request.session.get('email_verified') and request.session.get('phone_verified'):
                from django.contrib.auth import get_user_model
                email = request.session.get('register_email')
                phone = request.session.get('register_phone')
                password = request.session.get('register_password')

                temp_username = str(uuid.uuid4())[:30]

                user = User.objects.create_user(username=temp_username, email=email, password=password)
                # Если есть поле phone в User, то записать туда
                # user.phone = phone
                # user.save()

                # Чистим сессию
                for key in ['register_email', 'register_phone', 'register_password', 'email_verified', 'phone_verified']:
                    if key in request.session:
                        del request.session[key]

                messages.success(request, 'Регистрация завершена! Теперь войдите в систему.')
                return redirect('login')

            else:
                # Если почему-то телефон подтверждён, а email нет (или наоборот) — редирект на нужный шаг
                return redirect('verify_email')

    return render(request, 'registration/verify_phone.html')


import random
import string

def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


def resend_email_code_view(request):
    email = request.session.get('register_email')
    if not email:
        messages.error(request, 'Сначала введите email для регистрации.')
        return redirect('register')

    email_code = generate_code()
    EmailVerificationCode.objects.create(email=email, code=email_code)
    send_mail(
        'Ваш новый код подтверждения email',
        f'Ваш код: {email_code}',
        'no-reply@example.com',
        [email],
    )
    messages.success(request, 'Новый код отправлен на ваш email.')
    return redirect('verify_email')

def resend_phone_code_view(request):
    phone = request.session.get('register_phone')
    if not phone:
        messages.error(request, 'Сначала введите телефон для регистрации.')
        return redirect('register')

    phone_code = generate_code()
    PhoneVerificationCode.objects.create(phone=phone, code=phone_code)
    send_sms(phone, f'Ваш новый код подтверждения: {phone_code}')
    messages.success(request, 'Новый код отправлен на ваш телефон.')
    return redirect('verify_phone')


from django.utils.text import slugify
from django.shortcuts import render, redirect
from django.contrib import messages
from allauth.socialaccount.models import SocialLogin
from .models import PhoneVerificationCode
from .utils import generate_code, send_sms

def phone_verification_start(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        if phone:
            code = generate_code()
            PhoneVerificationCode.objects.create(phone=phone, code=code)
            send_sms(phone, f'Ваш код подтверждения: {code}')
            request.session['phone_to_verify'] = phone
            messages.success(request, 'Код отправлен на ваш телефон')
            return redirect('phone_verification_confirm')

    return render(request, 'registration/phone_verification_start.html')

import uuid
from django.contrib.auth import login
def phone_verification_confirm(request):
    phone = request.session.get('phone_to_verify')
    if not phone:
        messages.error(request, 'Сначала введите номер телефона')
        return redirect('phone_verification_start')

    if request.method == 'POST':
        code = request.POST.get('code')
        record = PhoneVerificationCode.objects.filter(phone=phone).order_by('-created_at').first()

        if not record or record.code != code or record.is_expired():
            messages.error(request, 'Неверный или истёкший код')
        else:
            # Восстанавливаем социальный логин из сессии
            sociallogin_data = request.session.get('socialaccount_sociallogin')
            if not sociallogin_data:
                messages.error(request, 'Данные соцсети не найдены. Попробуйте войти снова.')
                return redirect('account_login')

            sociallogin = SocialLogin.deserialize(sociallogin_data)
            user = sociallogin.user

            user.username = str(uuid.uuid4())


            user.phone = phone
            user.is_verified = True
            user.save()

            # Сохраняем соцлогин (создаст пользователя и войдёт)
            sociallogin.save(request)

            #оно не логинит, но в бд добавяляет, поэтому вызывал данную функцию возможно сработате, у меня просто аккаунты для тестов закончились
            #login(request, user, backend='django.contrib.auth.backends.ModelBackend')



            # Чистим сессию
            del request.session['socialaccount_sociallogin']
            del request.session['phone_to_verify']

            messages.success(request, 'Телефон подтверждён, вы успешно вошли!')
            return redirect('home')

    return render(request, 'registration/phone_verification_confirm.html', {'phone': phone})



from .forms import EmailChangeForm, EmailCodeConfirmForm
from .models import EmailChangeCode
from .utils import send_verification_code
from django.contrib import messages

@login_required
def change_email_request(request):
    if request.method == 'POST':
        form = EmailChangeForm(request.POST)
        if form.is_valid():
            new_email = form.cleaned_data['new_email']
            code = generate_code()

            # Сохраняем код
            EmailChangeCode.objects.filter(user=request.user).delete()
            EmailChangeCode.objects.create(user=request.user, new_email=new_email, code=code)

            # Отправляем код на почту

            send_verification_code(new_email, code)

            messages.info(request, 'Код подтверждения отправлен на новую почту.')
            return redirect('confirm_email_code')
    else:
        form = EmailChangeForm()

    return render(request, 'profile/change_email.html', {'form': form})

@login_required
def confirm_email_code(request):
    if request.method == 'POST':
        form = EmailCodeConfirmForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                email_change = EmailChangeCode.objects.get(user=request.user, code=code)
                if email_change.is_expired():
                    email_change.delete()
                    messages.error(request, 'Код истёк.')
                    return redirect('change_email_request')

                # Обновляем email
                request.user.email = email_change.new_email
                request.user.save()
                email_change.delete()

                messages.success(request, 'Почта успешно обновлена.')
                return redirect('profile_view')

            except EmailChangeCode.DoesNotExist:
                messages.error(request, 'Неверный код.')
    else:
        form = EmailCodeConfirmForm()

    return render(request, 'profile/confirm_email.html', {'form': form})



from .models import PhoneChangeCode
from .forms import PhoneChangeForm, PhoneCodeConfirmForm
from django.contrib import messages

@login_required
def change_phone_request(request):
    if request.method == 'POST':
        form = PhoneChangeForm(request.POST)
        if form.is_valid():
            new_phone = form.cleaned_data['new_phone']
            code = generate_code()

            # Удаляем старые коды
            PhoneChangeCode.objects.filter(user=request.user).delete()
            # Создаём новый
            PhoneChangeCode.objects.create(user=request.user, new_phone=new_phone, code=code)

            # Отправляем SMS на текущий телефон (или на новый — реши сам; по ТЗ отправляем на текущий)
            message = f'Ваш код подтверждения смены номера: {code}'
            send_sms(new_phone, message)


            messages.info(request, 'Код подтверждения отправлен на новый  номер телефона.')
            return redirect('confirm_phone_code')
    else:
        form = PhoneChangeForm()

    return render(request, 'profile/change_phone.html', {'form': form})

@login_required
def confirm_phone_code(request):
    if request.method == 'POST':
        form = PhoneCodeConfirmForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                phone_change = PhoneChangeCode.objects.get(user=request.user, code=code)
                if phone_change.is_expired():
                    phone_change.delete()
                    messages.error(request, 'Код истёк.')
                    return redirect('change_phone_request')

                # Обновляем номер телефона
                request.user.phone = phone_change.new_phone
                request.user.save()
                phone_change.delete()

                messages.success(request, 'Номер телефона успешно обновлён.')
                return redirect('profile_view')

            except PhoneChangeCode.DoesNotExist:
                messages.error(request, 'Неверный код.')
    else:
        form = PhoneCodeConfirmForm()

    return render(request, 'profile/confirm_phone.html', {'form': form})


from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import CustomPasswordChangeForm


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Чтобы не выбрасывало из сессии
            messages.success(request, 'Пароль успешно изменён.')
            return redirect('profile_view')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'profile/change_password.html', {'form': form})
