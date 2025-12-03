from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, UserProfileSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserSerializer
        return UserProfileSerializer

    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_object(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy']:
            return self.request.user
        return super().get_object()

    @action(detail=False, methods=['get'])
    def me(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=401)

        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """Альтернативный эндпоинт для регистрации"""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, *args, **kwargs):
        """Стандартный create (регистрация) с возвратом токенов"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Создаем JWT токены
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class APISignUpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        # Просто перенаправляем на существующий метод
        viewset = UserViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        return viewset.create(request)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken


class CustomLoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)

            return Response({
                'success': True,
                'access_token': str(refresh.access_token),  # ← Явно access_token
                'refresh_token': str(refresh),  # ← Явно refresh_token
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            })

        return Response({
            'success': False,
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)

        # Переименовываем поля для фронта
        data = {
            'access_token': response.data.get('access'),
            'refresh_token': response.data.get('refresh'),
            'success': True,
            'user': {
                # Можно добавить базовую информацию о пользователе
                'username': request.user.username if request.user.is_authenticated else None
            }
        }

        return Response(data)