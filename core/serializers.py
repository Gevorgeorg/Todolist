from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_repeat = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'password_repeat']

    def validate(self, attrs: dict) -> dict:
        if attrs.get('password') != attrs.get('password_repeat'):
            raise serializers.ValidationError({"password_repeat": "Пароли не совпадают"})
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop('password_repeat')
        user: User = User.objects.create_user(**validated_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class PasswordUpdateSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])

    def validate_old_password(self, value: str) -> str:
        user: User = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль некорректен")
        return value
