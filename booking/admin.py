from django.contrib import admin
from .models import User, Property, PropertyPhoto, Amenity, PropertyAmenity, Booking, Payment, Review, UserRating, AvailabilityCalendar, Notification, Message

# Регистрируем модель User в админке
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone', 'role', 'is_verified')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    list_filter = ('role', 'is_verified')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'avatar_url')}),
        ('Permissions', {'fields': ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone', 'password1', 'password2'),
        }),
    )

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'property_type', 'price_per_night', 'is_active', 'created_at')
    search_fields = ('title', 'owner__email', 'address', 'city')
    list_filter = ('property_type', 'is_active', 'city')
    date_hierarchy = 'created_at'

@admin.register(PropertyPhoto)
class PropertyPhotoAdmin(admin.ModelAdmin):
    list_display = ('property', 'is_primary', 'order_index')
    search_fields = ('property__title',)
    list_filter = ('is_primary',)

@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PropertyAmenity)
class PropertyAmenityAdmin(admin.ModelAdmin):
    list_display = ('property', 'amenity')
    search_fields = ('property__title', 'amenity__name')
    list_filter = ('amenity',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'property', 'check_in_date', 'check_out_date', 'total_price', 'status')
    search_fields = ('tenant__email', 'property__title', 'status')
    list_filter = ('status', 'check_in_date')
    date_hierarchy = 'created_at'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('booking', 'amount', 'payment_method', 'status')
    search_fields = ('booking__property__title', 'status')
    list_filter = ('status', 'payment_method')
    date_hierarchy = 'created_at'

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'property', 'rating', 'created_at')
    search_fields = ('author__email', 'property__title', 'comment')
    list_filter = ('rating',)
    date_hierarchy = 'created_at'

@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    list_display = ('from_user', 'to_user', 'rating')
    search_fields = ('from_user__email', 'to_user__email')
    list_filter = ('rating',)
    date_hierarchy = 'created_at'

@admin.register(AvailabilityCalendar)
class AvailabilityCalendarAdmin(admin.ModelAdmin):
    list_display = ('property', 'date', 'is_available', 'price')
    search_fields = ('property__title',)
    list_filter = ('is_available', 'date')
    date_hierarchy = 'date'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'is_read')
    search_fields = ('user__email', 'type', 'message')
    list_filter = ('is_read', 'type')
    date_hierarchy = 'created_at'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'booking', 'is_read')
    search_fields = ('sender__email', 'receiver__email', 'booking__property__title')
    list_filter = ('is_read',)
    date_hierarchy = 'created_at'