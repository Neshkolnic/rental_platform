import os

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.files.storage import default_storage
from .models import User, Property, PropertyPhoto, AvailabilityCalendar

from .models import User, Property, PropertyPhoto
from multiupload.fields import MultiFileField

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Email')

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True  # Ключевая строка для множественного выбора

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)


class PropertyForm(forms.ModelForm):
    photos = MultiFileField(
        min_num=0,
        max_num=17,
        max_file_size=1024 * 1024 * 10,  # 10MB
        label='Фотографии объекта',
        required=False,
        help_text='Первая загруженная фотография будет основной. Максимум 17 фото.'
    )

    latitude = forms.DecimalField(required=False, widget=forms.HiddenInput())
    longitude = forms.DecimalField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = Property
        exclude = ['owner', 'latitude', 'longitude']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['is_active'].initial = True
        self.fields['is_active'].widget = forms.HiddenInput()

    def save(self, commit=True, owner=None):
        property_obj = super().save(commit=False)
        if owner:
            property_obj.owner = owner

        if commit:
            property_obj.save()
            self.save_photos(property_obj)

        return property_obj

    def save_photos(self, property_obj):
        photos = self.cleaned_data.get('photos', [])
        print(f"Фотографий для сохранения: {len(photos)}")  # Отладочный вывод

        for i, photo in enumerate(photos):
            # Создаем уникальное имя файла
            ext = os.path.splitext(photo.name)[1]
            filename = f"property_{property_obj.id}_photo_{i}{ext}"

            # Сохраняем файл в хранилище
            path = default_storage.save(f'property_photos/{filename}', photo)

            # Создаем запись в базе данных
            PropertyPhoto.objects.create(
                property=property_obj,
                image=path,
                is_primary=(i == 0),
                order_index=i
            )
            print(f"Сохранено фото {i + 1}: {path}")  # Отладочный вывод

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

from .models import AvailabilityCalendar
class AvailabilityCalendarForm(forms.ModelForm):
    class Meta:
        model = AvailabilityCalendar
        fields = ['date', 'is_available', 'price']


from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


# forms.py

from django import forms
from .models import User

class ProfileForm(forms.ModelForm):
    # avatar_file = forms.FileField(required=False, label="Фото (аватар)")

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar']

