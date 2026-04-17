from django import forms

class StudentLoginForm(forms.Form):
    first_name = forms.CharField(max_length=50, label='Имя')
    last_name = forms.CharField(max_length=50, label='Фамилия')

class TeacherLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')
