from django.contrib.auth.models import User
from django.db import models

class Seminar(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveSmallIntegerField(blank=True)
    count = models.PositiveSmallIntegerField(blank=True)
    # time =
    online = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class UserSeminar(models.Model):
    user = models.ForeignKey(User, null=True, related_name='user_seminar', on_delete=models.SET_NULL)
    seminar = models.ForeignKey(Seminar, null=True, related_name='user_seminar', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
