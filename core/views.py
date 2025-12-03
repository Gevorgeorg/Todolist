from rest_framework import generics, permissions, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import update_last_login
from .serializers import (
    LoginSerializer,
    SignupSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
    PasswordUpdateSerializer
)

User = get_user_model()


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # ВАЖНО: эта строка отключает CSRF
        setattr(request, '_dont_enforce_csrf_checks', True)

        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(request, username=username, password=password)

            if user:
                login(request, user)
                update_last_login(None, user)

                return Response({
                    'username': user.username,
                    'password': password,
                }, status=status.HTTP_201_CREATED)

            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        user = request.user
        serializer = ProfileSerializer(user)
        return Response(serializer.data)

    def put(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        user = request.user
        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(user).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        user = request.user
        serializer = ProfileUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(ProfileSerializer(user).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)
        logout(request)
        return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)


class SignupView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SignupSerializer

    def create(self, request, *args, **kwargs):
        # ВАЖНО: эта строка отключает CSRF
        setattr(request, '_dont_enforce_csrf_checks', True)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return Response({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'password': request.data.get('password', ''),
            'password_repeat': request.data.get('password_repeat', ''),
        }, status=status.HTTP_201_CREATED)


class UpdatePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        return self._update_password(request)

    def patch(self, request):
        return self._update_password(request)

    def _update_password(self, request):
        setattr(request, '_dont_enforce_csrf_checks', True)

        serializer = PasswordUpdateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()

            login(request, user)

            return Response({
                'old_password': serializer.validated_data['old_password'],
                'new_password': serializer.validated_data['new_password']
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SocialAuthSuccessView(APIView):
    """Обработка успешной авторизации через соцсеть"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            from .serializers import ProfileSerializer
            return Response({
                'success': True,
                'user': ProfileSerializer(request.user).data,
                'message': 'Successfully authenticated with social network'
            })
        return Response({
            'success': False,
            'error': 'User not authenticated'
        }, status=401)


class SocialAuthErrorView(APIView):
    """Обработка ошибки авторизации через соцсеть"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'success': False,
            'error': 'Social authentication failed',
            'message': request.GET.get('message', 'Unknown error')
        }, status=400)