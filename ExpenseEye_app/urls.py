from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from expenses import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('expenses/', include('expenses.urls')),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.user_register, name='register'),
]
