from django import forms
from .models import Test, Tag



class StudentLoginForm(forms.Form):
    first_name = forms.CharField(max_length=50, label='Имя')
    last_name = forms.CharField(max_length=50, label='Фамилия')

class TeacherLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='Логин')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')

class CreateTestForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Test
        fields = ['title', 'description', 'tags']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        
class QuestionForm(forms.Form):
    question_text = forms.CharField(label='Текст вопроса', widget=forms.Textarea(attrs={'rows': 3}))
    num_answers = forms.ChoiceField(
        label='Количество вариантов ответа',
        choices=[(2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6')],
        initial=4,
        widget=forms.Select(attrs={'id': 'num_answers', 'hx-get': '/get-answer-fields/', 'hx-target': '#answers-container'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Будем добавлять поля для ответов динамически в зависимости от num_answers
        num = int(self.data.get('num_answers', 4)) if self.is_bound else 4
        for i in range(1, num + 1):
            self.fields[f'answer_{i}'] = forms.CharField(label=f'Вариант {i}', required=True)
        self.fields['correct_answer'] = forms.ChoiceField(
            label='Правильный ответ',
            choices=[(i, f'Вариант {i}') for i in range(1, num + 1)],
            widget=forms.RadioSelect
        )