from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from expenses import views
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('', redirect_to_login),
    path('login/', views.home, name='login'),
    path('register/', views.user_register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('admin/', admin.site.urls),
    path('expenses/', include('expenses.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('overview/', views.overview, name='overview'),
    path('budget/', views.budget, name='budget'),
    path('goals/', views.goals, name='goals'),
    path('reports/', views.reports, name='reports'),
    path('settings/', views.settings, name='settings'),
]
