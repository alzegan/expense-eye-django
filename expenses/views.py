from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string
from .models import Expense, Category, FinancialGoal, Profile
from expenses.forms import ExpenseFilterForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .forms import ExpenseForm, UserRegistrationForm, ExpenseFilterForm, FinancialGoalForm, UserUpdateForm
from django.db.models import Q, Sum, Avg, Max, Count
from django.utils import timezone
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.http import JsonResponse
from decimal import Decimal
from django.contrib import messages
import json
from django.views.generic import TemplateView
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from django.utils.decorators import method_decorator
from django.core.exceptions import ObjectDoesNotExist

MONTHS_PL = {
    1: 'Styczeń',
    2: 'Luty',
    3: 'Marzec',
    4: 'Kwiecień',
    5: 'Maj',
    6: 'Czerwiec',
    7: 'Lipiec',
    8: 'Sierpień',
    9: 'Wrzesień',
    10: 'Październik',
    11: 'Listopad',
    12: 'Grudzień'
}


def home(request):
    storage = messages.get_messages(request)
    storage.used = True

    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Nieprawidłowa nazwa użytkownika lub hasło.')
    else:
        form = AuthenticationForm()
        form.fields['username'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'Nazwa użytkownika'
        })
        form.fields['password'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'Hasło',
            'type': 'password'
        })
    return render(request, 'login_page.html', {'form': form})


def user_register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'register_page.html', {'form': form})


@login_required
def dashboard(request):
    current_month = timezone.now().month
    current_year = timezone.now().year
    formatted_date = f"{MONTHS_PL[current_month]} {current_year}"

    monthly_expenses = Expense.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    )
    total_month = monthly_expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    recent_expenses = Expense.objects.filter(
        user=request.user
    ).select_related('category').order_by('-date', '-id')[:5]

    expenses_by_category = Expense.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    financial_goals = FinancialGoal.objects.filter(
        user=request.user,
        archived=False,
        deadline__gte=timezone.now()
    ).order_by('deadline')[:3]

    context = {
        'total_month': total_month,
        'recent_expenses': recent_expenses,
        'expenses_by_category': expenses_by_category,
        'current_month': formatted_date,
        'financial_goals': financial_goals,
    }

    response = render(request, 'expenses/dashboard.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def budget(request):
    return render(request, 'expenses/budget.html')


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if request.POST.get('category') == 'new':
            new_category_name = request.POST.get('new_category')
            if new_category_name:
                category, created = Category.objects.get_or_create(name=new_category_name.strip())

                expense = Expense(
                    user=request.user,
                    amount=request.POST.get('amount'),
                    date=request.POST.get('date'),
                    description=request.POST.get('description', ''),
                    payment_method=request.POST.get('payment_method'),
                    category=category
                )
                expense.save()
                return redirect('dashboard')
        else:
            if form.is_valid():
                expense = form.save(commit=False)
                expense.user = request.user
                expense.save()

    else:
        form = ExpenseForm()

    return render(request, 'expenses/add_expense.html', {'form': form})


@login_required
def delete_expense(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    return render(request, 'expenses/delete_expense.html', {'expenses': expenses})


@login_required
def delete_expense_confirm(request, expense_id):
    if request.method == 'POST':
        try:
            expense = get_object_or_404(Expense, id=expense_id, user=request.user)
            expense.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@login_required
def modify_expense(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')
    categories = Category.objects.all()
    return render(request, 'expenses/modify_expense.html', {
        'expenses': expenses,
        'categories': categories
    })


@login_required
def get_expense(request, expense_id):
    try:
        expense = get_object_or_404(Expense, id=expense_id, user=request.user)
        return JsonResponse({
            'amount': str(expense.amount),
            'date': expense.date.strftime('%Y-%m-%d'),
            'category': expense.category.id,
            'description': expense.description or ''
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@csrf_exempt
def modify_expense_confirm(request, expense_id):
    if request.method == 'POST':
        try:
            expense = get_object_or_404(Expense, id=expense_id, user=request.user)
            data = json.loads(request.body)

            expense.amount = Decimal(data.get('amount'))
            expense.date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
            expense.category = get_object_or_404(Category, id=int(data.get('category')))
            expense.description = data.get('description', '')
            expense.save()

            return JsonResponse({
                'success': True,
                'message': 'Wydatek został zaktualizowany'
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'Wystąpił błąd podczas modyfikacji wydatku',
                'error': str(e)
            }, status=400)

    return JsonResponse({
        'success': False,
        'message': 'Nieprawidłowa metoda'
    }, status=405)


@login_required
def filters(request):
    expenses = Expense.objects.filter(user=request.user)
    form = ExpenseFilterForm(request.GET)

    if form.is_valid():
        if form.cleaned_data['min_amount']:
            expenses = expenses.filter(amount__gte=form.cleaned_data['min_amount'])
        if form.cleaned_data['max_amount']:
            expenses = expenses.filter(amount__lte=form.cleaned_data['max_amount'])
        if form.cleaned_data['category']:
            expenses = expenses.filter(category=form.cleaned_data['category'])
        if form.cleaned_data['date_from']:
            expenses = expenses.filter(date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data['date_to']:
            expenses = expenses.filter(date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data['description']:
            expenses = expenses.filter(description__icontains=form.cleaned_data['description'])

    return render(request, 'expenses/filters.html', {
        'expenses': expenses,
        'form': form
    })


@login_required
def goals(request):
    user_goals = FinancialGoal.objects.filter(
        user=request.user,
        archived=False
    ).order_by('deadline')

    if request.method == 'POST':
        form = FinancialGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('goals')
    else:
        form = FinancialGoalForm()

    return render(request, 'expenses/goals.html', {
        'goals': user_goals,
        'form': form
    })


@login_required
def update_goal_progress(request, goal_id):
    if request.method == 'POST' or 'GET':
        try:
            goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
            amount = Decimal(request.POST.get('amount', '0'))
            goal.current_amount += amount
            goal.save()

            goal_achieved = goal.check_if_achieved()

            return JsonResponse({
                'success': True,
                'new_amount': float(goal.current_amount),
                'progress': goal.get_progress_percentage(),
                'remaining': float(goal.get_remaining_amount()),
                'goal_achieved': goal_achieved,
                'archived': goal.archived
            })

        except Exception as e:
            print(f"Error updating goal: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    return JsonResponse({'success': False}, status=405)


@login_required
def delete_goal(request, goal_id):
    if request.method == 'POST':
        try:
            goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
            goal.delete()
            print(f"Goal {goal_id} deleted successfully")
            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error deleting goal: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    return JsonResponse({'success': False}, status=405)


@login_required
def achieved_goals(request):
    achieved_goals = FinancialGoal.objects.filter(
        user=request.user,
        archived=True
    ).order_by('-achieved_date')
    return render(request, 'expenses/achieved_goals.html', {
        'achieved_goals': achieved_goals
    })


@method_decorator(login_required, name='dispatch')
class ReportView(TemplateView):
    template_name = 'expenses/reports.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        period = int(self.request.GET.get('period', 30))
        category_id = self.request.GET.get('category')

        end_date = timezone.now()
        start_date = end_date - timedelta(days=period)

        expenses = Expense.objects.filter(
            user=self.request.user,
            date__range=(start_date, end_date)
        )

        if category_id:
            expenses = expenses.filter(category_id=category_id)

        stats = expenses.aggregate(
            total_expenses=Sum('amount'),
            max_expense=Max('amount')
        )

        total = stats['total_expenses'] or Decimal('0')
        avg_daily = total / period if total > 0 else Decimal('0')

        categories = Category.objects.filter(
            expense__user=self.request.user
        ).distinct()

        category_summary = []
        for cat in categories:
            cat_expenses = expenses.filter(category=cat)
            cat_total = cat_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0')

            if total > 0:
                percentage = (cat_total / total * 100).quantize(Decimal('0.1'))
            else:
                percentage = Decimal('0')

            category_summary.append({
                'name': cat.name,
                'total': cat_total,
                'percentage': percentage,
                'count': cat_expenses.count()
            })

        context.update({
            'categories': categories,
            'total_expenses': stats['total_expenses'] or 0,
            'max_expense': stats['max_expense'] or 0,
            'avg_daily': round(avg_daily, 2),
            'category_summary': category_summary,
            'expenses': expenses.order_by('-date')[:50],
            'selected_period': period,
            'selected_category': category_id,
        })

        return context


@login_required
def settings(request):
    try:
        profile = request.user.profile
    except ObjectDoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        if 'profile_image' in request.FILES:
            try:
                profile.image = request.FILES['profile_image']
                profile.save()
                messages.success(request, 'Zdjęcie profilowe zostało zaktualizowane!')
            except Exception as e:
                messages.error(request, 'Wystąpił błąd podczas aktualizacji zdjęcia.')
            return redirect('account_settings')

        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Twój profil został zaktualizowany!')
                return redirect('account_settings')
            else:
                messages.error(request, 'Wystąpił błąd podczas aktualizacji profilu.')

        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Twoje hasło zostało zmienione!')
                return redirect('account_settings')
            else:
                messages.error(request, 'Wystąpił błąd podczas zmiany hasła.')
                return render(request, 'expenses/account_settings.html', {
                    'user_form': UserUpdateForm(instance=request.user),
                    'password_form': password_form,
                })

    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    context = {
        'user_form': user_form,
        'password_form': password_form,
    }

    return render(request, 'expenses/account_settings.html', context)


def password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )

            subject = 'Reset hasła - ExpenseEye'
            message = render_to_string('reset_password_email.html', {
                'user': user,
                'reset_url': reset_url
            })

            send_mail(subject, message, 'noreply@expenseeye.com', [email])
            messages.success(request, 'Link do resetowania hasła został wysłany na podany adres email.')
        else:
            messages.error(request, 'Nie znaleziono użytkownika o podanym adresie email.')

    return render(request, 'password_reset.html')


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

        if request.method == 'POST':
            password = request.POST.get('new_password')
            if password:
                user.set_password(password)
                user.save()
                messages.success(request, 'Hasło zostało zmienione.')
                return redirect('login')

        if default_token_generator.check_token(user, token):
            return render(request, 'password_reset_confirm.html')

    except:
        pass

    messages.error(request, 'Link do resetowania hasła jest nieprawidłowy.')
    return redirect('login')
