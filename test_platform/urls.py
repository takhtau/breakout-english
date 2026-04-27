from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView
from tests import views as tests_views

urlpatterns = [
    path('accounts/logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('', lambda request: redirect('/tests/')),
    path('tests/', include('tests.urls')),
    path('register/invite/<str:code>/', tests_views.register_by_invite, name='register_by_invite'),
]
