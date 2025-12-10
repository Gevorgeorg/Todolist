from django.db import transaction
from flask_restx import ValidationError
from rest_framework import serializers
from .models import GoalCategory, Goal, GoalComment, Board, BoardParticipant
from core.models import User
from core.serializers import ProfileSerializer


class GoalCategorySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.filter(is_deleted=False),
        required=True
    )

    class Meta:
        model = GoalCategory
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "user")

    def validate_board(self, board):
        if board.is_deleted:
            raise serializers.ValidationError("Доска удалена")

        # ПРОВЕРЯЕМ ПРАВА!
        request = self.context.get('request')
        if request:
            user = request.user

            # Проверяем что пользователь владелец или редактор
            has_permission = BoardParticipant.objects.filter(
                user=user,
                board=board,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                board__is_deleted=False
            ).exists()

            if not has_permission:
                raise serializers.ValidationError(
                    "Только владелец или редактор могут создавать категории"
                )

        return board


class GoalCommentCreateSerializer(serializers.ModelSerializer):
    """Простой сериализатор для создания комментариев"""

    class Meta:
        model = GoalComment
        fields = ['text', 'goal']

    def create(self, validated_data):
        """Добавляем пользователя из запроса"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)

class GoalCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = GoalComment
        fields = ["id", "text", "user", "user_username", "goal", "created", "updated"]
        read_only_fields = ("id", "created", "updated", "user", "user_username")

    def get_user(self, obj):
        """Возвращаем объект пользователя с id и username"""
        return {
            "id": obj.user.id,
            "username": obj.user.username
        }




class GoalSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    comments = GoalCommentSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Goal
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "user")

    def validate_category(self, category):
        if category.is_deleted:
            raise serializers.ValidationError("Категория удалена")
        if category.board.is_deleted:
            raise serializers.ValidationError("Доска категории удалена")

        # ПРОВЕРЯЕМ ПРАВА!
        request = self.context.get('request')
        if request:
            user = request.user

            # Проверяем что пользователь владелец или редактор
            has_permission = BoardParticipant.objects.filter(
                user=user,
                board=category.board,
                role__in=[BoardParticipant.Role.owner, BoardParticipant.Role.writer],
                board__is_deleted=False
            ).exists()

            if not has_permission:
                raise serializers.ValidationError(
                    "Только владелец или редактор могут создавать цели"
                )

        return category


class BoardCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        read_only_fields = ("id", "created", "updated")
        fields = "__all__"

    def create(self, validated_data):
        user = validated_data.pop("user")
        board = Board.objects.create(**validated_data)
        BoardParticipant.objects.create(
            user=user, board=board, role=BoardParticipant.Role.owner
        )
        return board


class BoardParticipantSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        required=True,
        choices=BoardParticipant.Role.choices[1:]  # без owner
    )
    user = serializers.SlugRelatedField(
        slug_field="username", queryset=User.objects.all()
    )

    class Meta:
        model = BoardParticipant
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "board")


class BoardSerializer(serializers.ModelSerializer):
    participants = BoardParticipantSerializer(many=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        fields = "__all__"
        read_only_fields = ("id", "created", "updated")

    def update(self, instance, validated_data):

        owner = self.context.get('request').user

        # Проверяем, что текущий пользователь - владелец
        is_owner = instance.participants.filter(
            user=owner,
            role=BoardParticipant.Role.owner
        ).exists()

        if not is_owner:
            raise ValidationError("Только владелец может редактировать доску")

        # Получаем участников
        participants_data = validated_data.pop("participants", [])

        # Преобразуем в словарь
        new_by_id = {part["user"].id: part for part in participants_data}

        # Получаем старых участников (кроме владельца)
        old_participants = instance.participants.exclude(user=owner)

        with transaction.atomic():
            # Обрабатываем старых участников
            for old_participant in old_participants:
                if old_participant.user_id not in new_by_id:
                    old_participant.delete()
                else:
                    if old_participant.role != new_by_id[old_participant.user_id]["role"]:
                        old_participant.role = new_by_id[old_participant.user_id]["role"]
                        old_participant.save()
                    new_by_id.pop(old_participant.user_id)

            # Добавляем новых участников
            for new_part in new_by_id.values():
                # Проверяем, что не добавляем владельца
                if new_part["role"] != BoardParticipant.Role.owner:
                    BoardParticipant.objects.create(
                        board=instance,
                        user=new_part["user"],
                        role=new_part["role"]
                    )

            # Обновляем заголовок
            if 'title' in validated_data:
                instance.title = validated_data["title"]
                instance.save()

        return instance


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = "__all__"
