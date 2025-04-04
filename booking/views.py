from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import UserRegisterForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from .forms import PropertyForm
from .models import Property
from django.http import JsonResponse
from geopy.geocoders import Nominatim


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

# def register_view(request):
#     if request.method == 'POST':
#         form = UserRegisterForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('home')
#     else:
#         form = UserRegisterForm()
#     return render(request, 'registration/register.html', {'form': form})
def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Указываем backend явно
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        else:
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
        form = PropertyForm(request.POST)
        if form.is_valid():
            property = form.save(commit=False)
            property.owner = request.user
            property.save()
            return redirect('property_list')  # Или на страницу успеха
    else:
        form = PropertyForm()

    return render(request, 'property/create.html', {'form': form})

# views.py
def property_list(request):
    properties = Property.objects.filter(is_active=True)
    return render(request, 'property/list.html', {'properties': properties})

@login_required
def my_properties(request):
    properties = Property.objects.filter(owner=request.user)
    return render(request, 'property/my_properties.html', {'properties': properties})