from django.db import transaction
from django.db.models import QuerySet
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from core.models import User
from rest_framework.request import Request
from goals.models import GoalCategory, Goal, GoalComment, Board, BoardParticipant
from goals.permissions import has_board_permissions


def check_board_write_permission(user: User, board: Board) -> bool:
    """Проверяет, имеет ли пользователь право на запись в доску (владелец/редактор)."""

    return has_board_permissions(
        user=user,
        board=board,
        required_roles=[BoardParticipant.Role.owner, BoardParticipant.Role.writer])


class GoalCategorySerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    board = serializers.PrimaryKeyRelatedField(
        queryset=Board.objects.filter(is_deleted=False),
        required=True)

    class Meta:
        model = GoalCategory
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "user")

    def validate_board(self, board: Board) -> Board:
        request: Request = self.context.get('request')
        if not request:
            return board

        if board.is_deleted:
            raise serializers.ValidationError("Доска удалена")

        if not check_board_write_permission(request.user, board):
            raise serializers.ValidationError("Только владелец или редактор могут создавать категории")

        return board


class GoalCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalComment
        fields = ['text', 'goal']

    def create(self, validated_data: dict) -> GoalComment:
        request: Request = self.context.get('request')
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

    def get_user(self, obj: GoalComment) -> dict:
        return {
            "id": obj.user.id,
            "username": obj.user.username
        }


class GoalSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    comments = GoalCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Goal
        fields = "__all__"
        read_only_fields = ("id", "created", "updated", "user")

    def validate_category(self, category: GoalCategory) -> GoalCategory:
        request: Request = self.context.get('request')
        if not request:
            return category

        if category.is_deleted:
            raise serializers.ValidationError("Категория удалена")
        if category.board.is_deleted:
            raise serializers.ValidationError("Доска категории удалена")

        if not check_board_write_permission(request.user, category.board):
            raise serializers.ValidationError("Только владелец или редактор могут создавать цели")

        return category


class BoardCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Board
        read_only_fields = ("id", "created", "updated")
        fields = "__all__"

    def create(self, validated_data: dict) -> Board:
        user: User = validated_data.pop("user")
        board: Board = Board.objects.create(**validated_data)
        BoardParticipant.objects.create(
            user=user, board=board, role=BoardParticipant.Role.owner
        )
        return board


class BoardParticipantSerializer(serializers.ModelSerializer):
    role: int = serializers.ChoiceField(
        required=True,
        choices=BoardParticipant.Role.choices[1:]
    )
    user: User = serializers.SlugRelatedField(
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

    @transaction.atomic
    def update(self, instance: Board, validated_data: dict) -> Board:
        request = self.context.get('request')
        if not request:
            raise ValidationError("Запрос недоступен")

        owner: User = request.user

        if not instance.participants.filter(user=owner, role=BoardParticipant.Role.owner).exists():
            raise ValidationError("Только владелец может редактировать доску")

        participants_data: list = validated_data.pop("participants", [])
        new_by_id: dict = {part["user"].id: part for part in participants_data}
        old_participants: QuerySet = instance.participants.exclude(user=owner)

        for old_participant in old_participants:
            user_id: int = old_participant.user_id
            if user_id not in new_by_id:
                old_participant.delete()
            else:
                new_role = new_by_id[user_id]["role"]
                if old_participant.role != new_role:
                    old_participant.role = new_role
                    old_participant.save()
                new_by_id.pop(user_id)

        for new_part in new_by_id.values():
            if new_part["role"] != BoardParticipant.Role.owner:
                BoardParticipant.objects.create(
                    board=instance,
                    user=new_part["user"],
                    role=new_part["role"]
                )

        if 'title' in validated_data:
            instance.title = validated_data.get("title")
            instance.save()

        return instance


class BoardListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = "__all__"
