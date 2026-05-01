from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('accounts/logout/', LogoutView.as_view(next_page='/tests/login/'), name='logout'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', lambda request: redirect('/tests/login/')),
    path('tests/', include('tests.urls')),
]