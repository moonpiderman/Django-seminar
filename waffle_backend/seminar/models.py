from django.contrib.auth.models import User
from django.db import models

class Seminar(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveSmallIntegerField(blank=True)
    count = models.PositiveSmallIntegerField(blank=True)
    time = models.TimeField(default='00:00')
    online = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserSeminar(models.Model):
    PARTICIPANT = 'participant'
    INSTRUCTOR = 'instructor'

    ROLE_CHOICES = (
        (PARTICIPANT, PARTICIPANT),
        (INSTRUCTOR, INSTRUCTOR),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True, default='')

    user = models.ForeignKey(User, null=True, related_name='user_seminar', on_delete=models.CASCADE)
    seminar = models.ForeignKey(Seminar, null=True, related_name='user_seminar', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    dropped_at = models.DateTimeField(null=True)
