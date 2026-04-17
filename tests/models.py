from django.db import models
from django.conf import settings

class Test(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    text = models.TextField()

    def __str__(self):
        return self.text[:50]

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text[:50]

class Result(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField()
    total = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name} - {self.test.title} - {self.score}/{self.total}"
        elif self.student:
            return f"{self.student.username} - {self.test.title} - {self.score}/{self.total}"
        else:
            return f"Anonymous - {self.test.title} - {self.score}/{self.total}"