from django.urls import path
from . import views

urlpatterns = [
    # ── Основные ──
    path('', views.test_list, name='test_list'),
    path('teacher/', views.teacher_home, name='teacher_home'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('login/', views.login_page, name='login_page'),

    # ── Тесты ──
    path('test/<int:test_id>/', views.test_entry, name='test_entry'),
    path('test/<int:test_id>/detail/', views.test_detail, name='test_detail'),
    path('test/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('test/<int:test_id>/results/', views.test_results, name='test_results'),
    path('test/<int:test_id>/questions/', views.test_questions, name='test_questions'),
    path('test/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('test/<int:test_id>/delete/', views.delete_test, name='delete_test'),
    path('test/<int:test_id>/delete-results/', views.delete_test_results, name='delete_test_results'),

    # ── Создание ──
    path('create/', views.create_test, name='create_test'),
    path('add-questions/<int:test_id>/', views.add_questions, name='add_questions'),

    # ── Результаты ──
    path('result/<int:result_id>/', views.test_result, name='test_result'),
    path('result/<int:result_id>/detail/', views.result_detail, name='result_detail'),
    path('result/<int:result_id>/delete/', views.delete_result, name='delete_result'),
    path('results/delete-all/', views.delete_all_results, name='delete_all_results'),

    # ── Вопросы ──
    path('question/<int:question_id>/edit/', views.edit_question, name='edit_question'),

    # ── Теги ──
    path('tags/', views.tags_list, name='tags_list'),
    path('tags/add/', views.tag_add, name='tag_add'),
    path('tags/add-inline/', views.tag_add_inline, name='tag_add_inline'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),

    # ── Пользователи ──
    path('users/', views.users_list, name='users_list'),
    path('users/change-role/<int:user_id>/', views.change_role, name='change_role'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # ── Инвайты ──
    path('register/invite/<uuid:code>/', views.register_by_invite, name='register_by_invite'),
    path('invite/delete/<int:invite_id>/', views.delete_invite, name='delete_invite'),
]