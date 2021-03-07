from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

# from django.contrib.auth.decorators import login_required
# from user.views import UserViewSet

from seminar.models import Seminar, UserSeminar
from seminar.serializers import SeminarSerializer, InstructorsOfSeminarSerializer


class SeminarViewSet(viewsets.GenericViewSet):
    queryset = Seminar.objects.all()
    serializer_class = SeminarSerializer
    permission_classes = (IsAuthenticated(), )

    def get_permissions(self):
        if self.action in ('create', 'update', 'user'):
            return (AllowAny(), )
        return self.permission_classes

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except InterruptedError:
            return Response({"error": "A seminar with that seminarname already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        data = serializer.data
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        user = request.user
        seminar = self.get_object()

        if not user.user_seminar.filter(seminar=seminar, role=UserSeminar.INSTRUCTOR).exists():
            Response({"error": "You're not charge in this seminar."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        serializer = self.get_serializer(seminar, data=data, partial=True)
        serializer.is_valid(raise_exception=True)


        serializer.update(seminar, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # @login_required
    @action(detail=True, methods=['POST', 'DELETE'])
    def user(self, request, pk):
        # user = self.request.user
        seminar = self.get_object()

        # if user is not None:
        #     UserViewSet.login(self, user)

        # if not self.request.user.is_authenticated:
        #     return Response({"error": "You must be login."}, status=status.HTTP_400_BAD_REQUEST)

        if self.request.method == 'POST':
            return self.join_seminar(seminar)
        elif self.request.method == 'DELETE' :
            return self.delete_seminar(seminar)


    def join_seminar(self, seminar):
        user = self.request.user
        role = self.request.data.get('role')

        if not role == 'participant' and not role == 'instructor':
            return Response({"error": "You need to put your role."}, status=status.HTTP_400_BAD_REQUEST)

        if user.user_seminar.filter(seminar=seminar).exists():
            return Response({"error": "Do not authenticate in a seminar."}, status=status.HTTP_403_FORBIDDEN)

        if role == UserSeminar.PARTICIPANT:
            add_capacity = seminar.now_capacity + 1
            if not hasattr(user, 'participant'):
                return Response({"error": "You're not a participant in a seminar."}, status=status.HTTP_403_FORBIDDEN)

            # acception check
            if not user.participant.accepted:
                return Response({"error": "You're not accepted in a seminar."}, status=status.HTTP_403_FORBIDDEN)

            # capacity 설정
            if add_capacity >= seminar.capacity:
                return Response({"error": "You cannot join this seminar."}, status=status.HTTP_400_BAD_REQUEST)

            elif add_capacity < seminar.capacity:
                seminar.now_capacity = add_capacity

            UserSeminar.objects.create(user=user, seminar=seminar, role=role)
            return Response({"Enroll in this seminar as a participant."}, status=status.HTTP_201_CREATED)

        elif role == UserSeminar.INSTRUCTOR:
            UserSeminar.objects.create(user=user, seminar=seminar, role=role)
            return Response({"Enroll in this seminar as a instructor."}, status=status.HTTP_201_CREATED)

    def delete_seminar(self, seminar):
        user = self.request.user

        user_seminar = user.user_seminar.filter(seminar=seminar).last()

        if user_seminar :
            user_seminar.dropped_at = timezone.now()
            user_seminar.is_active = False
            user_seminar.save()

        seminar.refresh_from_db()
        return Response(self.get_serializer(seminar).data)
