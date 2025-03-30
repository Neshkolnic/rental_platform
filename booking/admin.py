from django.contrib import admin
from .models import User, SocialAuth, Property, PropertyPhoto, Amenity, PropertyAmenity, Booking, Payment, Review, UserRating, AvailabilityCalendar, Notification, Message

# Регистрируем модель User в админке
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_verified', 'created_at', 'updated_at')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('role', 'is_verified', 'created_at')


@admin.register(SocialAuth)
class SocialAuthAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'provider_id')
    search_fields = ('user__email', 'provider')


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'property_type', 'price_per_night', 'is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'owner__email', 'address', 'city')
    list_filter = ('property_type', 'is_active', 'city')


@admin.register(PropertyPhoto)
class PropertyPhotoAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'order_index')
    search_fields = ('property__title',)


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PropertyAmenity)
class PropertyAmenityAdmin(admin.ModelAdmin):
    list_display = ('property', 'amenity')
    search_fields = ('property__title', 'amenity__name')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'property', 'check_in_date', 'check_out_date', 'total_price', 'status', 'created_at', 'updated_at')
    search_fields = ('tenant__email', 'property__title', 'status')
    list_filter = ('status', 'created_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status', 'created_at')
    search_fields = ('booking__property__title', 'status')
    list_filter = ('status', 'created_at')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'property', 'rating', 'created_at')
    search_fields = ('author__email', 'property__title', 'comment')


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'rating', 'created_at')
    search_fields = ('from_user__email', 'to_user__email')
    list_filter = ('rating', 'created_at')


@admin.register(AvailabilityCalendar)
class AvailabilityCalendarAdmin(admin.ModelAdmin):
    list_display = ('property', 'date', 'is_available', 'price')
    search_fields = ('property__title', 'date')
    list_filter = ('is_available', 'date')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'is_read', 'created_at')
    search_fields = ('user__email', 'type', 'message')
    list_filter = ('is_read', 'created_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'booking', 'is_read', 'created_at')
    search_fields = ('sender__email', 'receiver__email', 'booking__property__title')
    list_filter = ('is_read', 'created_at')

