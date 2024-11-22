from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from .models import Expense, Category, FinancialGoal
from expenses.forms import ExpenseFilterForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .forms import ExpenseForm, UserRegistrationForm, ExpenseFilterForm, FinancialGoalForm
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from datetime import datetime
import json


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
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login_page.html', {'form': form})
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
@csrf_exempt  # Tymczasowo dla testów
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
            print(f"Error: {str(e)}")  # Debug
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
    if request.method == 'POST':
        try:
            goal = get_object_or_404(FinancialGoal, id=goal_id, user=request.user)
            data = json.loads(request.body)
            amount = Decimal(str(data.get('amount', 0)))

            goal.current_amount = goal.current_amount + amount

            # Sprawdź czy cel został osiągnięty
            if goal.current_amount >= goal.target_amount:
                goal.archived = True
                goal.achieved_date = timezone.now()

            goal.save()

            remaining = goal.get_remaining_amount()
            progress = goal.get_progress_percentage()

            return JsonResponse({
                'success': True,
                'new_amount': float(goal.current_amount),
                'remaining': float(remaining),
                'progress': progress,
                'goal_achieved': goal.archived
            })
        except Exception as e:
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
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False}, status=405)

@login_required
def reports(request):
    return render(request, 'expenses/reports.html')


@login_required
def settings(request):
    return render(request, 'expenses/settings.html')
