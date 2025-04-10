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
    return render(request, 'property/list.html', {'properties': properties})


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


