from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User
from .models import Property


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Email')


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type',
            'room_count', 'guest_capacity', 'price_per_night',
            'address', 'city', 'country'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.TextInput(attrs={
                'id': 'address-input',
                'placeholder': 'Введите полный адрес'
            }),
        }

    def clean(self):
         cleaned_data = super().clean()
         # Можно добавить дополнительную валидацию адреса
         return cleaned_data