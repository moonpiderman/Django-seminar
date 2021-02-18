from django.contrib.auth.models import User
from django.db import models

class ParticipnatProfile(models.Model):
    user = models.OneToOneField(User, null=True, related_name='participant', on_delete=models.SET_NULL)
    university = models.CharField(max_length=50, blank=True)
    accepted = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, null=True, related_name='instructor', on_delete=models.SET_NULL)
    company = models.CharField(max_length=50, blank=True)
    year = models.PositiveSmallIntegerField(default=0, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)