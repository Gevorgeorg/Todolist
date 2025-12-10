from rest_framework import permissions

from goals.models import BoardParticipant, Board, GoalComment


class BoardPermission(permissions.BasePermission):
    """
    Универсальный пермишен для работы с досками
    """

    def has_object_permission(self, request, view, obj):
        # Получаем доску из объекта
        board = self._get_board_from_obj(obj)
        if not board:
            return False

        # Если объект - комментарий, особые правила
        if isinstance(obj, GoalComment):
            return self._check_comment_permission(request, obj, board)

        # Для остальных объектов
        if request.method in permissions.SAFE_METHODS:
            # Для просмотра - любая роль
            required_roles = None
        else:
            # Для изменения - только владелец или редактор
            required_roles = [
                BoardParticipant.Role.owner,
                BoardParticipant.Role.writer
            ]

        return self._check_board_permission(request.user, board, required_roles)

    def _check_comment_permission(self, request, comment, board):
        """Проверка прав для комментариев"""
        user = request.user

        # 1. Всегда разрешаем GET, HEAD, OPTIONS (просмотр)
        if request.method in permissions.SAFE_METHODS:
            # Любой участник доски может просматривать комментарии
            return self._check_board_permission(user, board, required_roles=None)

        # 2. Для PUT, PATCH, DELETE (изменение/удаление):
        #    - Автор комментария может
        #    - Владелец или редактор доски может
        #    - Читатель - не может

        # Автор может всегда (даже если он читатель)
        if comment.user == user:
            return True

        # Владелец или редактор может
        required_roles = [
            BoardParticipant.Role.owner,
            BoardParticipant.Role.writer
        ]

        return self._check_board_permission(user, board, required_roles)

    def _get_board_from_obj(self, obj):
        """Получает объект доски из разных типов объектов"""
        # Вариант 1: объект - GoalComment (комментарий)
        if isinstance(obj, GoalComment):
            return obj.goal.category.board  # ← ДОБАВИЛИ ЭТО!

        # Вариант 2: объект - GoalCategory (у него есть board)
        if hasattr(obj, 'board'):
            return obj.board  # GoalCategory.board

        # Вариант 3: объект - Goal (у него есть category)
        elif hasattr(obj, 'category'):
            # Проверяем что у категории есть board
            if hasattr(obj.category, 'board'):
                return obj.category.board  # Goal.category.board

        # Вариант 4: объект - сама Board
        elif isinstance(obj, Board):  # Проверяем тип объекта
            return obj  # Сам объект и есть доска

        return None

    def _check_board_permission(self, user, board, required_roles=None):
        """
        Проверяет права пользователя на доску

        Args:
            user: пользователь
            board: объект доски
            required_roles: список требуемых ролей (None - любая роль)

        Returns:
            bool: имеет ли пользователь права
        """
        query = BoardParticipant.objects.filter(
            user=user,
            board=board,
            board__is_deleted=False
        )

        if required_roles:
            query = query.filter(role__in=required_roles)

        return query.exists()