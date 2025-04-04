from django.db import models
from django.contrib.auth.models import AbstractUser
from geopy.geocoders import Nominatim


class User(AbstractUser):
    # Все ваши текущие поля остаются
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar_url = models.CharField(max_length=512, blank=True, null=True)
    role = models.CharField(max_length=50, default='user')
    password = models.CharField(max_length=128, blank=True)  # Временное поле
    is_verified = models.BooleanField(default=False)
    # created_at и updated_at уже есть в AbstractUser

    # Указываем, что email будет использоваться как идентификатор для входа
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Обязательные поля при создании пользователя

    def __str__(self):
        return self.username or self.email

class SocialAuth(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=50)
    provider_id = models.CharField(max_length=255)

class Property(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    property_type = models.CharField(max_length=50)
    room_count = models.IntegerField()
    guest_capacity = models.IntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.address and (not self.latitude or not self.longitude):
            self.geocode_address()
        super().save(*args, **kwargs)

    def geocode_address(self):
        """Автозаполнение координат через Яндекс API"""
        import requests
        from django.conf import settings

        try:
            response = requests.get(
                'https://geocode-maps.yandex.ru/1.x/',
                params={
                    'geocode': self.address,
                    'apikey': settings.YANDEX_MAPS_API_KEY,
                    'format': 'json'
                }
            )
            data = response.json()
            pos = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            self.longitude, self.latitude = map(float, pos.split())
        except:
            # Если геокодирование не сработало - оставляем NULL
            pass

class PropertyPhoto(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    url = models.CharField(max_length=512)
    is_primary = models.BooleanField(default=False)
    order_index = models.IntegerField()

class Amenity(models.Model):
    name = models.CharField(max_length=100)

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)

class Booking(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=255)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    rating = models.SmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class UserRating(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rating = models.SmallIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class AvailabilityCalendar(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    date = models.DateField()
    is_available = models.BooleanField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
