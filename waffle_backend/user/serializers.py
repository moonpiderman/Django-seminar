from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from seminar.models import UserSeminar
from user.models import ParticipantProfile, InstructorProfile
from seminar.serializers import SeminarFromInstructor, SeminarFromParticipant


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(allow_blank=False)
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    participant = serializers.SerializerMethodField()
    instructor = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'last_login',
            'date_joined',
            # 'token',
            'participant',
            'instructor',
        )

    def validate_password(self, value):
        return make_password(value)

    def validate(self, data):
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        if bool(first_name) ^ bool(last_name):
            raise serializers.ValidationError("First name and last name should appear together.")
        if first_name and last_name and not (first_name.isalpha() and last_name.isalpha()):
            raise serializers.ValidationError("First name or last name should not have number.")

        return data

    @transaction.atomic
    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        Token.objects.create(user=user)
        return user

    def get_participant(self, user):
        if hasattr(user, 'participant'):
            return ParticipantProfileSerializer(user.participant, context=self.context).data
        return None

    def get_instructor(self, user):
        if hasattr(user, 'instructor'):
            return InstructorProfileSerializer(user.instructor, context=self.context).data
        return None

class ParticipantProfileSerializer(serializers.ModelSerializer):
    seminars = serializers.SerializerMethodField()

    class Meta :
        model = ParticipantProfile
        fields = (
            'id',
            'university',
            'accepted',
            'seminars',
        )

    def get_seminars(self, participant_profile):
        participant_seminars = participant_profile.user.user_seminar.filter(role=UserSeminar.PARTICIPANT)
        if participant_profile:
            return SeminarFromParticipant(participant_seminars, many=True, context=self.context).data
        return None

class InstructorProfileSerializer(serializers.ModelSerializer):
    charge = serializers.SerializerMethodField()

    class Meta :
        model = InstructorProfile
        fields = (
            'id',
            'company',
            'year',
            'charge',
        )

    def get_charge(self, instructor_profile):
        instructor_seminars = instructor_profile.user.user_seminar.filter(role=UserSeminar.INSTRUCTOR).last()
        if instructor_profile:
            return SeminarFromInstructor(instructor_seminars, context=self.context).data
        return None
