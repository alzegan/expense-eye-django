from django import forms
from .models import Expense, Category, FinancialGoal
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
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
    new_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Wpisz nazwę nowej kategorii'
        })
    )

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
                'type': 'date'
            }),
            'category': forms.Select(attrs={
                'class': 'form-input'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-input',
                'choices': [
                    ('cash', 'Gotówka'),
                    ('card', 'Karta'),
                    ('transfer', 'Przelew'),
                    ('other', 'Inne')
                ]
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3,
                'placeholder': 'Opisz wydatek...'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        categories = Category.objects.all().order_by('name')  # Dodano order_by
        self.fields['category'].choices = [('', '--------')] + [(c.id, c.name) for c in categories] + [('new', 'Dodaj inną kategorię...')]
        self.fields['date'].input_formats = ['%Y-%m-%d']
        self.fields['date'].initial = timezone.now().strftime('%Y-%m-%d')
        self.fields['description'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('category') == 'new':
            if not self.data.get('new_category'):
                raise forms.ValidationError("Proszę podać nazwę nowej kategorii")
        return cleaned_data


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class ExpenseFilterForm(forms.Form):
    min_amount = forms.DecimalField(required=False, label="Minimalna kwota")
    max_amount = forms.DecimalField(required=False, label="Maksymalna kwota")
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="----",
        label="Kategoria"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data od"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Data do"
    )
    description = forms.CharField(
        required=False,
        label="Opis zawiera"
    )

class FinancialGoalForm(forms.ModelForm):
    class Meta:
        model = FinancialGoal
        fields = ['name', 'target_amount', 'deadline']
        labels = {
            'name': 'Cel',
            'target_amount': 'Kwota',
            'deadline': 'Termin realizacji'
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Nazwa celu'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            })
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Wprowadź imię'
        })
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Wprowadź nazwisko'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Wprowadź email'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError('Ten adres email jest już zajęty.')
        return email

