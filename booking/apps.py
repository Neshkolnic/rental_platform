from django.apps import AppConfig

class BookingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'booking'

    def ready(self):
        # Подключаем сигналы для отслеживания входа пользователей
        import booking.signals  # Здесь мы подключаем сигналы для обработки событий после авторизации
