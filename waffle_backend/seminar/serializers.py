from django.contrib.auth.models import User
from rest_framework import serializers

from seminar.models import Seminar, UserSeminar


class SeminarSerializer(serializers.ModelSerializer):
    time = serializers.TimeField(format='%H:%M', input_formats=['%H:%M'])
    instructors = serializers.SerializerMethodField()
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'capacity',
            'count',
            'time',
            'online',
            'instructors',
            'participants',
        )

    def get_instructors(self, seminar):
        instructors_seminar = seminar.user_seminar.filter(role=UserSeminar.INSTRUCTOR)
        return InstructorsOfSeminarSerializer(instructors_seminar, many=True, context=self.context).data

    def get_participants(self, seminar):
        participants_seminar = seminar.user_seminar.filter(role=UserSeminar.PARTICIPANT)
        return ParticipantsOfSeminarSerializer(participants_seminar, many=True, context=self.context).data

class QueryParamsSerializer(serializers.ModelSerializer):
    instructors = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Seminar
        fields = (
            'id',
            'name',
            'instructors',
            'participant_count',
        )

    def get_instructors(self, seminar):
        instructors_seminar = seminar.user_seminar.filter(role=UserSeminar.INSTRUCTOR)
        return InstructorsOfSeminarSerializer(instructors_seminar, many=True, context=self.context).data
    def get_participant_count(self, seminar):
        return seminar.user_seminars.filter(role=UserSeminar.PARTICIPANT, is_active=True).count()


class InstructorsOfSeminarSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    joined_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'joined_at',
        )

class ParticipantsOfSeminarSerializer(serializers.ModelSerializer):
    joined_at = serializers.DateTimeField(source='created_at')
    id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.EmailField(source='user.email')

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'joined_at',
            'is_active',
            'dropped_at',
        )

 # connect with User
class SeminarFromInstructor(serializers.ModelSerializer):
    id = serializers.IntegerField(source='seminar.id')
    name = serializers.CharField(source='seminar.name')
    joined_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'name',
            'joined_at',
        )

class SeminarFromParticipant(serializers.ModelSerializer):
    id = serializers.IntegerField(source='seminar.id')
    name = serializers.CharField(source='seminar.name')
    joined_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = UserSeminar
        fields = (
            'id',
            'name',
            'joined_at',
            'is_active',
            'dropped_at',
        )