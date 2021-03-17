from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError

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
    role = serializers.ChoiceField(write_only=True, choices=UserSeminar.ROLES)
    university = serializers.CharField(write_only=True, allow_blank=True, required=False)
    accepted = serializers.BooleanField(write_only=True, default=True, required=False)
    company = serializers.CharField(write_only=True, allow_blank=True, required=False)
    year = serializers.IntegerField(write_only=True, required=False)

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
            'role',
            'university',
            'accepted',
            'company',
            'year',
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

        role = data.get('role')
        if role == UserSeminar.PARTICIPANT:
            profile_serializer = ParticipantProfileSerializer(data=data, context=self.context)
            profile_serializer.is_valid(raise_exception=True)

        elif role == UserSeminar.INSTRUCTOR:
            profile_serializer = InstructorProfileSerializer(data=data, context=self.context)
            profile_serializer.is_valid(raise_exception=True)
        else:
            raise serializers.ValidationError("You insert wrong role name.")
            # return Response({"error": "wrong role."}, status=status.HTTP_400_BAD_REQUEST)

        # profile_serializer.is_valid(raise_exception=True)
        return data

    @transaction.atomic
    def create(self, validated_data):
        role = validated_data.pop('role')
        university = validated_data.pop('university', '')
        accepted = validated_data.pop('accepted', None)
        company = validated_data.pop('company', '')
        year = validated_data.pop('year', None)

        user = super(UserSerializer, self).create(validated_data)
        Token.objects.create(user=user)

        if role == UserSeminar.PARTICIPANT:
            ParticipantProfile.objects.create(user=user, university=university, accepted=accepted)
        elif role == UserSeminar.INSTRUCTOR:
            InstructorProfile.objects.create(user=user, company=company, year=year)
        else:
            return Response({"error": "Wrong role."}, status=status.HTTP_400_BAD_REQUEST)
        return user

    @transaction.atomic
    def update(self, user, validated_data):
        if hasattr(user, 'participant'):
            profile_participant = user.participant
            university = validated_data.get('university')

            if university is not None :
                profile_participant.university = university
                profile_participant.save()

        if hasattr(user, 'instructor'):
            profile_instructor = user.instructor
            company = validated_data.get('company')
            year = validated_data.get('year')

            if company is not None or year:
                if company is not None :
                    profile_instructor.company = company
                if year >= 0:
                    profile_instructor.year = year
                profile_instructor.save()

        print(user.username)
        return super(UserSerializer, self).update(user, validated_data)

    def get_participant(self, user):
        if hasattr(user, 'participant'):
            return ParticipantProfileSerializer(user.participant, context=self.context).data
        return None

    def get_instructor(self, user):
        if hasattr(user, 'instructor'):
            return InstructorProfileSerializer(user.instructor, context=self.context).data
        return None

class ParticipantProfileSerializer(serializers.ModelSerializer):
    accepted = serializers.BooleanField(default=True, required=False)
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
        return SeminarFromParticipant(participant_seminars, many=True, context=self.context).data
        # if participant_seminars:
        #     return SeminarFromParticipant(participant_seminars, many=True, context=self.context).data
        # return None

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
        # return SeminarFromInstructor(instructor_seminars, context=self.context).data
        if instructor_seminars:
            return SeminarFromInstructor(instructor_seminars, context=self.context).data
        return None
