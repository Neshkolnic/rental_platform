from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User, Property, PropertyPhoto

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Email')

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        attrs = attrs or {}
        attrs['multiple'] = 'multiple'
        super().__init__(attrs)

    def value_from_datadict(self, data, files, name):
        return files.getlist(name)

class PropertyForm(forms.ModelForm):
    photos = forms.FileField(
        widget=MultipleFileInput(attrs={
            'class': 'photo-input',
            'accept': 'image/*'
        }),
        label='Фотографии объекта',
        required=False,
        help_text='Первая загруженная фотография будет основной. Максимум 17 фото.'
    )

    class Meta:
        model = Property
        exclude = ['owner', 'latitude', 'longitude']  # Исключаем ненужные поля

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Улучшенная обработка поля is_active
        self.fields['is_active'].initial = True
        self.fields['is_active'].widget = forms.HiddenInput()

    def clean_photos(self):
        photos = self.files.getlist('photos') if 'photos' in self.files else []
        if len(photos) > PropertyPhoto.MAX_PHOTOS:
            raise forms.ValidationError(f'Максимум {PropertyPhoto.MAX_PHOTOS} фотографий')

        for photo in photos:
            if not photo.content_type.startswith('image/'):
                raise forms.ValidationError(f'{photo.name} - не изображение')
            if photo.size > 10 * 1024 * 1024:
                raise forms.ValidationError(f'{photo.name} слишком большой (максимум 10MB)')
        return photos

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')