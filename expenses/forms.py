from django import forms
from .models import Expense, Category
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __int__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'Nazwa użytkownika'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'Email'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'Hasło'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'Powtórz hasło'
        })


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['amount', 'date', 'category', 'description', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date',
                'value': timezone.now().strftime('%Y-%m-%d')  # Format RRRR-MM-DD
            }),
            'category': forms.Select(attrs={
                'class': 'form-input'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-input'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Opisz wydatek...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].initial = timezone.now().strftime('%Y-%m-%d')
        self.fields['description'].required = False


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
