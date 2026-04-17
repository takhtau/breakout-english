from django.urls import path
from . import views

urlpatterns = [
    path('test/<int:test_id>/', views.test_entry, name='test_entry'),
    path('', views.test_list, name='test_list'),
    path('<int:test_id>/', views.test_detail, name='test_detail'),
    path('<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('result/<int:result_id>/', views.test_result, name='test_result'),
    path('test/<int:test_id>/results/', views.test_results, name='test_results'),
]
