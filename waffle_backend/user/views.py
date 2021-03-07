from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from user.models import ParticipantProfile, InstructorProfile

from user.serializers import UserSerializer, ParticipantProfileSerializer


class UserViewSet(viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, )

    def get_permissions(self):
        if self.action in ('create', 'login'):
            return (AllowAny(), )
        return self.permission_classes

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            return Response({"error": "A user with that username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        role = request.data.get('role')

        # seminar = request.data.get('seminar')

        university = request.data.get('university') or ""
        accepted = request.data.get('accepted')
        company = request.data.get('company') or ""
        year = request.data.get('year') or ""

        if role != 'participant' and role != 'instructor':
            return Response({"error": "You did not insert role."}, status=status.HTTP_400_BAD_REQUEST)

        elif role == 'participant':
            ParticipantProfile.objects.create(user=user, university=university, accepted=accepted)
            # UserSeminar.objects.create(user=user, role=role)

        elif role == 'instructor':
            InstructorProfile.objects.create(user=user, company=company, year=year)
            # UserSeminar.objects.create(user=user, role=role, seminar=seminar)

        serializer.save()

        login(request, user)

        data = serializer.data
        data['token'] = user.auth_token.key
        return Response(data, status=status.HTTP_201_CREATED)


    @action(detail=False, methods=['PUT'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # token 값 출력해주기 (JSON)
            data = self.get_serializer(user).data
            token, created = Token.objects.get_or_create(user=user)
            data['token'] = token.key
            return Response(data)

        return Response({"error": "Wrong username or wrong password"}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['POST'])
    def logout(self, request):
        logout(request)
        return Response()

    def retrieve(self, request, pk=None):
        user = request.user if pk == 'me' else self.get_object()
        return Response(self.get_serializer(user).data)


    def update(self, request, pk=None):
        if pk != 'me':
            return Response({"error": "Can't update other Users information"}, status=status.HTTP_403_FORBIDDEN)

        user = request.user

        role = request.data.get('role')

        university = request.data.get('university') or ""
        accepted = request.data.get('accepted')
        company = request.data.get('company') or ""
        year = request.data.get('year') or ""

        if role != 'participant' and role != 'instructor':
            return Response({"error": "You did not insert role."}, status=status.HTTP_400_BAD_REQUEST)

        elif role == 'participant':
            ParticipantProfile.objects.filter(user_id=user.id).update(university=university, accepted=accepted)

        elif role == 'instructor':
            InstructorProfile.objects.filter(user_id=user.id).update(company=company, year=year)

        user.save()

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.update(user, serializer.validated_data)
        return Response(serializer.data)

    @action(detail=False, methods=['POST'])
    def participant(self, request):
        user = request.user

        university = request.data.get('university')
        accepted = request.data.get('accepted')

        if hasattr(user, 'participant'):
            return Response({"error": "You're already a participant"}, status=status.HTTP_400_BAD_REQUEST)


        ParticipantProfile.objects.create(university=university, accepted=accepted, user_id=user.id)

        return Response({"new participant from instructor."}, status=status.HTTP_201_CREATED)
