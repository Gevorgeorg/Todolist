from rest_framework import permissions
from core.models import User
from goals.models import Board, BoardParticipant, Goal, GoalCategory, GoalComment
from rest_framework.request import Request


def has_board_permissions(user: User, board: Board, required_roles: list | None) -> bool:
    """Проверяет, есть ли у пользователя доступ к доске с указанными ролями"""

    queryset = BoardParticipant.objects.filter(
        user=user,
        board=board,
        board__is_deleted=False
    )
    if required_roles is not None:
        queryset = queryset.filter(role__in=required_roles)
    return queryset.exists()


class BoardPermission(permissions.BasePermission):
    WRITE_ROLES = [BoardParticipant.Role.owner, BoardParticipant.Role.writer]

    def _get_board_from_object(self, obj) -> Board | None:
        """Извлекает объект доски из переданного объекта (доска, категория, цель, комментарий)"""

        if isinstance(obj, Board):
            return obj
        if isinstance(obj, GoalComment):
            return obj.goal.category.board
        if isinstance(obj, Goal):
            return obj.category.board
        if isinstance(obj, GoalCategory):
            return obj.board
        return None

    def has_object_permission(self, request: Request, view, obj) -> bool:
        """Проверяет доступ к возможности редактировать обьекты"""

        board = self._get_board_from_object(obj)
        if not board:
            return False

        if isinstance(obj, GoalComment):
            return self._check_comment_permission(request, obj, board)

        required_roles = None if request.method in permissions.SAFE_METHODS else self.WRITE_ROLES
        return has_board_permissions(request.user, board, required_roles)

    def _check_comment_permission(self, request: Request, comment: GoalComment, board: Board) -> bool:
        """Проверяет доступ к возможности редактировать комментарии, даже reader должен иметь возможность редактировать свой коммент"""

        user: User = request.user

        if request.method in permissions.SAFE_METHODS:
            return has_board_permissions(user, board, required_roles=None)

        if comment.user == user:
            return True

        return has_board_permissions(user, board, required_roles=self.WRITE_ROLES)
