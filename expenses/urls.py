from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('budget/', views.budget, name='budget'),
    path('budget/add/', views.add_expense, name='add_expense'),
    path('budget/delete/', views.delete_expense, name='delete_expense'),
    path('budget/delete_expense_confirm/<int:expense_id>/', views.delete_expense_confirm,
         name='delete_expense_confirm'),
    path('budget/modify_expense/', views.modify_expense, name='modify_expense'),
    path('budget/get_expense/<int:expense_id>/', views.get_expense, name='get_expense'),
    path('budget/modify_expense_confirm/<int:expense_id>/', views.modify_expense_confirm,
         name='modify_expense_confirm'),
    path('filters/', views.filters, name='filters'),
    path('goals/', views.goals, name='goals'),
    path('goals/<int:goal_id>/update/', views.update_goal_progress, name='update_goal_progress'),
    path('goals/<int:goal_id>/delete/', views.delete_goal, name='delete_goal'),
    path('achieved_goals/', views.achieved_goals, name='achieved_goals'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
]