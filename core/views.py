from rest_framework import permissions, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from .models import User
from .serializers import (SignupSerializer,
                          ProfileSerializer,
                          PasswordUpdateSerializer)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        user: User = authenticate(request, **request.data)

        if not user:
            return Response({"error": "Неверные данные"}, status=401)

        login(request, user)
        return Response({"username": user.username})


class ProfileView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self) -> User:
        return self.request.user

    def get_serializer_context(self) -> dict:
        return {'request': self.request}

    def perform_destroy(self, instance) -> None:
        logout(self.request)


class SignupView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer


class UpdatePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request: Request) -> Response:
        serializer = PasswordUpdateSerializer(
            data=request.data,
            context={'request': request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user: User = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        update_session_auth_hash(request, user)

        return Response({
            'message': 'Пароль успешно изменен'
        }, status=status.HTTP_200_OK)
