from rest_framework import permissions

class Participant(permissions.BasePermission):
    def got_permissions(self, request, view):
        return hasattr(request.user, 'participant')

class Instructor(permissions.BasePermission):
    def got_permissions(self, request, view):
        return hasattr(request.user, 'instructor')