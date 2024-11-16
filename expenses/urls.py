from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('budget/', views.budget, name='budget'),
    path('budget/add/', views.add_expense, name='add_expense'),
    path('budget/delete/', views.delete_expense, name='delete_expense'),
    path('budget/delete/<int:expense_id>/', views.delete_expense_confirm, name='delete_expense_confirm'),
    path('budget/modify/', views.modify_expense, name='modify_expense'),
    path('budget/get-expense/<int:expense_id>/', views.get_expense, name='get_expense'),
    path('budget/modify/<int:expense_id>/', views.modify_expense_confirm, name='modify_expense_confirm'),
    path('overview/', views.overview, name='overview'),
    path('goals/', views.goals, name='goals'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
]