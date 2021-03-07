from django.db import transaction
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from seminar.models import Seminar, UserSeminar
from seminar.serializers import SeminarSerializer, QueryParamsSerializer
from user.permissions import Participant, Instructor


class SeminarViewSet(viewsets.GenericViewSet):
    queryset = Seminar.objects.all()
    serializer_class = SeminarSerializer
    permission_classes = (IsAuthenticated, )

    def get_permissions(self):
        if self.action in ('create', 'update'):
            return (Instructor(), )
        elif self.action == 'user' and self.action == 'DELETE':
            return (Participant(), )
        return super(SeminarViewSet, self).get_permissions()

    def get_serializer_class(self):
        if self.action == 'list':
            return QueryParamsSerializer
        return self.serializer_class

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

    def retrieve(self, request, pk=None):
        seminar = self.get_object()
        return Response(self.get_serializer(seminar).data)

    def update(self, request, pk=None):
        user = request.user
        seminar = self.get_object()

        if not user.user_seminar.filter(seminar=seminar, role=UserSeminar.INSTRUCTOR).exists():
            Response({"error": "You're not charge in this seminar."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data

        serializer = self.get_serializer(seminar, data=data, partial=True)
        serializer.is_valid(raise_exception=True)

        participant_count = seminar.user_seminar.filter(role=UserSeminar.PARTICIPANT, is_active=True).count()
        if data.get('capacity') and int(data.get('capacity')) < participant_count:
            return Response({"error": "Capacity is forbidden"}, status=status.HTTP_400_BAD_REQUEST)


        serializer.update(seminar, serializer.validated_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def list(self, request):
        name = request.query_params.get('name')
        order = request.query_params.get('order')

        seminar = self.get_queryset()

        if name:
            seminar = seminar.filter(name__icontains='name')

        if order == 'earliest':
            seminar = seminar.order_by('created_at')
        else :
            seminar = seminar.order_by('-created_at')

        return Response(self.get_serializer(seminar, many=True).data)

    # @login_required
    @action(detail=True, methods=['POST', 'DELETE'])
    def user(self, request, pk):
        seminar = self.get_object()

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
            return Response({"error": "You already join this seminar."}, status=status.HTTP_403_FORBIDDEN)

        if role == UserSeminar.PARTICIPANT:

            if not hasattr(user, 'participant'):
                return Response({"error": "You're not a participant in a seminar."}, status=status.HTTP_403_FORBIDDEN)

            if not user.participant.accepted:
                return Response({"error": "You are not accepted."}, status=status.HTTP_403_FORBIDDEN)

            with transaction.atomic():
                participant_count = seminar.user_seminar.select_for_update().filter(
                    role=UserSeminar.PARTICIPANT, is_active=True).count()
                if participant_count >= seminar.capacity:
                    return Response({"error": "This seminar is full."}, status=status.HTTP_400_BAD_REQUEST)

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
