from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from expenses import views
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def redirect_to_login(request):
    return redirect('login')

urlpatterns = [
    path('', redirect_to_login),
    path('admin/', admin.site.urls),
    path('login/', views.home, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('expenses.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)