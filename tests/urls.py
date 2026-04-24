from django.urls import path
from . import views

urlpatterns = [
    path('teacher/', views.teacher_home, name='teacher_home'),
    path('test/<int:test_id>/', views.test_entry, name='test_entry'),
    path('', views.test_list, name='test_list'),
    path('<int:test_id>/', views.test_detail, name='test_detail'),
    path('<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('result/<int:result_id>/', views.test_result, name='test_result'),
    path('test/<int:test_id>/results/', views.test_results, name='test_results'),
    path('create/', views.create_test, name='create_test'),
    path('add-questions/<int:test_id>/', views.add_questions, name='add_questions'),
    path('test/<int:test_id>/questions/', views.test_questions, name='test_questions'),
    path('test/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('result/<int:result_id>/detail/', views.result_detail, name='result_detail'),
    path('tags/', views.tags_list, name='tags_list'),
    path('tags/add/', views.tag_add, name='tag_add'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    path('test/<int:test_id>/delete/', views.delete_test, name='delete_test'),
    path('users/', views.users_list, name='users_list'),
    path('users/change-role/<int:user_id>/', views.change_role, name='change_role'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
]
