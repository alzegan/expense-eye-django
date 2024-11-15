from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('budget/', views.budget, name='budget'),
    path('overview/', views.overview, name='overview'),
    path('goals/', views.goals, name='goals'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
]