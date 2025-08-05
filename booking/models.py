from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.conf import settings
import requests
from datetime import date


from django.core.files.storage import default_storage

class User(AbstractUser):
    class Role(models.TextChoices):
        USER = 'user', 'User'
        HOST = 'host', 'Host'
        ADMIN = 'admin', 'Admin'
        BLOG_EDITOR = 'blog_editor', 'Blog Editor'

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=50, choices=Role.choices, default=Role.USER)
    password = models.CharField(max_length=128, blank=True)
    is_verified = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    is_support = models.BooleanField(default=False)
    telegram_id = models.CharField(max_length=50, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        try:
            old = User.objects.get(pk=self.pk)
        except User.DoesNotExist:
            old = None

        super().save(*args, **kwargs)

        if old and old.avatar and old.avatar != self.avatar:
            if default_storage.exists(old.avatar.path):
                default_storage.delete(old.avatar.path)

    def delete(self, *args, **kwargs):
        if self.avatar and default_storage.exists(self.avatar.path):
            default_storage.delete(self.avatar.path)
        super().delete(*args, **kwargs)

    # в модели User добавь метод

    def get_all_reviews(self):
        reviews_about_user = self.reviews_received.all()
        user_properties = self.properties.all()  # если related_name='properties' в модели Property для owner
        reviews_about_properties = Review.objects.filter(property__in=user_properties, review_type='property')
        return reviews_about_user | reviews_about_properties

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name or self.email


class SocialAuth(models.Model):
    class Provider(models.TextChoices):
        GOOGLE = 'google', 'Google'
        FACEBOOK = 'facebook', 'Facebook'
        APPLE = 'apple', 'Apple'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_auth')
    provider = models.CharField(max_length=50, choices=Provider.choices)
    provider_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('provider', 'provider_id')

    def __str__(self):
        return f"{self.user.email} - {self.provider}"


class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = 'apartment', 'Apartment'
        HOUSE = 'house', 'House'
        VILLA = 'villa', 'Villa'
        CABIN = 'cabin', 'Cabin'
        COTTAGE = 'cottage', 'Cottage'
        LOFT = 'loft', 'Loft'

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=255)
    is_published = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    description = models.TextField()
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    review_count = models.PositiveIntegerField(default=0)
    property_type = models.CharField(max_length=50, choices=PropertyType.choices)
    room_count = models.PositiveIntegerField()
    guest_capacity = models.PositiveIntegerField()
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.address and (not self.latitude or not self.longitude):
            self.geocode_address()
        super().save(*args, **kwargs)

    def geocode_address(self):
        # Геокодирование для получения координат
        try:
            response = requests.get(
                'https://geocode-maps.yandex.ru/1.x/',
                params={
                    'geocode': self.address,
                    'apikey': settings.YANDEX_MAPS_API_KEY,  # Ваш ключ API
                    'format': 'json'
                }
            )
            data = response.json()
            pos = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            self.longitude, self.latitude = map(float, pos.split())
        except Exception as e:
            print(f"Geocoding failed: {e}")

    @property
    def primary_photo(self):
        return self.photos.filter(is_primary=True).first() or self.photos.first()

    @property
    def available_dates(self):
        return self.availability.filter(is_available=True, date__gte=date.today())

    def __str__(self):
        return f"{self.title} in {self.city}"


class PropertyPhoto(models.Model):
    MAX_PHOTOS = 17

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='property_photos/%Y/%m/%d/', null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    order_index = models.IntegerField(default=0)

    class Meta:
        ordering = ['order_index']


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name='property_amenities')

    class Meta:
        unique_together = ('property', 'amenity')
        verbose_name_plural = 'Property Amenities'

    def __str__(self):
        return f"{self.property.title} - {self.amenity.name}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        COMPLETED = 'completed', 'Completed'

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    review_reminder_sent = models.BooleanField(default=False)

    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.check_in_date >= self.check_out_date:
            raise ValidationError('Check-out date must be after check-in date')

        overlapping_bookings = Booking.objects.filter(
            property=self.property,
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
            status__in=[Booking.Status.CONFIRMED, Booking.Status.PENDING]
        ).exclude(pk=self.pk)

        if overlapping_bookings.exists():
            raise ValidationError('This property is already booked for selected dates')

    def save(self, *args, **kwargs):
        old_status = None
        if self.pk:
            old_booking = Booking.objects.filter(pk=self.pk).first()
            if old_booking:
                old_status = old_booking.status

        super().save(*args, **kwargs)

        # Если статус изменился на подтвержденный — отправить напоминание через 3 секунды (для теста)
        if old_status != self.status and self.status == self.Status.CONFIRMED:
            schedule_review_reminder(self.id, delay_seconds=3)

        # Если статус изменился на завершённый — отправить напоминание (для продакшена)
        if old_status != self.status and self.status == self.Status.COMPLETED:
            schedule_review_reminder(self.id, delay_seconds=3)  # delay можно убрать или сделать 0


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    class Method(models.TextChoices):
        CARD = 'card', 'Credit Card'
        PAYPAL = 'paypal', 'PayPal'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=Method.choices)
    transaction_id = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} for Booking #{self.booking.id}"


# class Review(models.Model):
#     author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
#     property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='reviews')
#     booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='review')
#     rating = models.PositiveSmallIntegerField()
#     comment = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         unique_together = ('booking', 'author')
#
#     def clean(self):
#         if not 1 <= self.rating <= 5:
#             raise ValidationError('Rating must be between 1 and 5')
#
#     def save(self, *args, **kwargs):
#         self.full_clean()
#         super().save(*args, **kwargs)
#
#     def __str__(self):
#         return f"Review by {self.author.full_name} for {self.property.title}"


class UserRating(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rating = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def clean(self):
        if not 1 <= self.rating <= 5:
            raise ValidationError('Rating must be between 1 and 5')

        if self.from_user == self.to_user:
            raise ValidationError('You cannot rate yourself')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rating from {self.from_user.full_name} to {self.to_user.full_name}"


class AvailabilityCalendar(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='availability')
    date = models.DateField()
    is_available = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ('property', 'date')
        verbose_name_plural = 'Availability Calendar'

    def __str__(self):
        return f"{self.property.title} on {self.date}: {'Available' if self.is_available else 'Booked'}"


class Notification(models.Model):
    class Type(models.TextChoices):
        BOOKING_REQUEST = 'booking_request', 'Booking Request'
        BOOKING_CONFIRMED = 'booking_confirmed', 'Booking Confirmed'
        BOOKING_CANCELLED = 'booking_cancelled', 'Booking Cancelled'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        REVIEW_RECEIVED = 'review_received', 'Review Received'
        MESSAGE_RECEIVED = 'message_received', 'Message Received'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=Type.choices)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()} notification for {self.user.full_name}"



class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver}"


from django.db import models
from django.conf import settings


from django.db import models
from django.conf import settings
from django.db.models import Avg

class Review(models.Model):
    REVIEW_TYPE_CHOICES = (
        ('property', 'Property'),       # отзыв об объекте недвижимости
        ('tenant', 'Tenant'),           # отзыв о арендаторе (владельцем)
        ('landlord', 'Landlord'),       # отзыв о собственнике (арендатором)
    )

    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='review')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_received', null=True, blank=True)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)

    review_type = models.CharField(max_length=10, choices=REVIEW_TYPE_CHOICES)

    rating = models.PositiveSmallIntegerField()  # от 1 до 5
    comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.review_type == 'property':
            # Пересчёт рейтинга недвижимости
            reviews = Review.objects.filter(property=self.property, review_type='property')
            total = reviews.count()
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

            self.property.average_rating = round(avg, 2)
            self.property.review_count = total
            self.property.save()
        elif self.review_type in ('tenant', 'landlord'):
            # Пересчёт рейтинга пользователя, если нужно
            user = self.to_user
            reviews = Review.objects.filter(to_user=user, review_type=self.review_type)
            total = reviews.count()
            avg = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0

            # Предположим, у пользователя есть поля average_rating и review_count (нужно добавить, если нет)
            user.average_rating = round(avg, 2)
            user.review_count = total
            user.save()

    def __str__(self):
        return f'Отзыв от {self.author} для {self.to_user if self.to_user else self.property}'
