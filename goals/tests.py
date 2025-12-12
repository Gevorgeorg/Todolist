import pytest
from goals.models import BoardParticipant, GoalComment, Goal, Status, Board, GoalCategory
from core.models import User
from rest_framework.test import APIClient


@pytest.fixture
def user() -> User:
    """Создаёт тестового пользователя"""

    return User.objects.create_user(
        username="user1",
        email="user1@example.com",
        password="pass123"
    )


@pytest.fixture
def another_user() -> User:
    """Создаёт тестового пользователя"""

    return User.objects.create_user(
        username="user2",
        email="user2@example.com",
        password="pass123"
    )


@pytest.fixture
def api_client() -> APIClient:
    """Возвращает клиент для API-запросов"""

    return APIClient()


@pytest.fixture
def board(user: User) -> Board:
    """Создает тестовую доску"""

    board = Board.objects.create(title="Test Board")
    BoardParticipant.objects.create(board=board, user=user, role=BoardParticipant.Role.owner)
    return board


@pytest.fixture
def category(user: User, board: Board) -> GoalCategory:
    """Создает тестовую категорию"""

    return GoalCategory.objects.create(title="Category 1", board=board, user=user)


@pytest.fixture
def goal(user: User, category: GoalCategory) -> Goal:
    """Создает тестовую цель"""

    return Goal.objects.create(title="Test Goal", category=category, user=user)


@pytest.fixture
def comment(user: User, goal: Goal) -> GoalComment:
    """Создает тестовый коммент"""

    return GoalComment.objects.create(text="Test comment", goal=goal, user=user)


@pytest.mark.django_db
def test_board_create(api_client: APIClient, user: User) -> None:
    """Тест создания доски"""

    api_client.force_login(user)
    response = api_client.post("/goals/board/create", {"title": "My Board"}, format="json")
    assert response.status_code == 201
    assert response.data["title"] == "My Board"
    assert "id" in response.data


@pytest.mark.django_db
def test_board_list(api_client: APIClient, user: User, board: Board) -> None:
    """Тестирует список досок с пагинацией"""

    api_client.force_login(user)
    response = api_client.get("/goals/board/list?limit=10")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1
    assert response.data["results"][0]["title"] == "Test Board"


@pytest.mark.django_db
def test_board_update(api_client: APIClient, user: User, board: Board) -> None:
    """Тестирует обновление доски"""

    api_client.force_login(user)
    response = api_client.put(
        f"/goals/board/{board.id}",
        {"title": "Updated Board", "participants": []},
        format="json"
    )
    assert response.status_code == 200
    assert response.data["title"] == "Updated Board"


@pytest.mark.django_db
def test_board_delete(api_client: APIClient, user: User, board: Board) -> None:
    """Тест удаления доски"""

    api_client.force_login(user)
    response = api_client.delete(f"/goals/board/{board.id}")
    assert response.status_code == 204
    board.refresh_from_db()
    assert board.is_deleted is True


@pytest.mark.django_db
def test_category_create(api_client: APIClient, user: User, board: Board) -> None:
    """Тест создания категории"""

    api_client.force_login(user)
    response = api_client.post(
        "/goals/goal_category/create",
        {"title": "Work", "board": board.id},
        format="json"
    )
    assert response.status_code == 201
    assert response.data["title"] == "Work"


@pytest.mark.django_db
def test_category_list(api_client: APIClient, user: User, category: GoalCategory) -> None:
    """тест вывода списка категорий с пагинацией"""

    api_client.force_login(user)
    response = api_client.get("/goals/goal_category/list?limit=10")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_category_delete(api_client: APIClient, user: User, category: GoalCategory) -> None:
    """Тест удаления категории"""

    Goal.objects.create(title="Test Goal", category=category, user=user)
    api_client.force_login(user)
    response = api_client.delete(f"/goals/goal_category/{category.id}")
    assert response.status_code == 204
    category.refresh_from_db()
    assert category.is_deleted is True
    assert Goal.objects.filter(category=category, status=Status.archived).exists()


@pytest.mark.django_db
def test_goal_create(api_client: APIClient, user: User, category: GoalCategory) -> None:
    """Тестирует создание цели в категории."""

    api_client.force_login(user)
    response = api_client.post(
        "/goals/goal/create",
        {"title": "Finish project", "category": category.id},
        format="json"
    )
    assert response.status_code == 201
    assert response.data["title"] == "Finish project"


@pytest.mark.django_db
def test_goal_list(api_client: APIClient, user: User, goal: Goal) -> None:
    """Тестирует получение списка целей с пагинацией."""

    api_client.force_login(user)
    response = api_client.get("/goals/goal/list?limit=10")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_goal_filter_by_category(api_client: APIClient, user: User, category: GoalCategory, goal: Goal) -> None:
    """Тестирует фильтрацию целей по категории"""

    api_client.force_login(user)
    response = api_client.get(f"/goals/goal/list?category={category.id}")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["title"] == "Test Goal"


@pytest.mark.django_db
def test_goal_delete(api_client: APIClient, user: User, goal: Goal) -> None:
    """Тестирует мягкое удаление цели (статус=archived)"""

    api_client.force_login(user)
    response = api_client.delete(f"/goals/goal/{goal.id}")
    assert response.status_code == 204
    goal.refresh_from_db()
    assert goal.status == Status.archived


@pytest.mark.django_db
def test_comment_create(api_client: APIClient, user: User, goal: Goal) -> None:
    """Тестирует создание комментария к цели"""

    api_client.force_login(user)
    response = api_client.post(
        "/goals/goal_comment/create",
        {"text": "Great!", "goal": goal.id},
        format="json"
    )
    assert response.status_code == 201
    assert response.data["text"] == "Great!"


@pytest.mark.django_db
def test_comment_list(api_client: APIClient, user: User, comment: GoalComment) -> None:
    """Тестирует получение списка комментариев с пагинацией"""

    api_client.force_login(user)
    response = api_client.get("/goals/goal_comment/list?limit=10")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_comment_update_author(api_client: APIClient, user: User, comment: GoalComment) -> None:
    """Тестирует обновление комментария автором"""

    api_client.force_login(user)
    response = api_client.patch(
        f"/goals/goal_comment/{comment.id}",
        {"text": "Updated comment"},
        format="json"
    )
    assert response.status_code == 200
    assert response.data["text"] == "Updated comment"


@pytest.mark.django_db
def test_comment_delete_author(api_client: APIClient, user: User, comment: GoalComment) -> None:
    """Тестирует удаление комментария автором"""

    api_client.force_login(user)
    response = api_client.delete(f"/goals/goal_comment/{comment.id}")
    assert response.status_code == 204


@pytest.mark.django_db
def test_comment_update_non_author_denied(api_client: APIClient, user: User, another_user: User, board: Board,
                                          goal: Goal) -> None:
    """Тестирует запрет редактирования комментария не автором"""

    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.reader)
    comment = GoalComment.objects.create(text="Owner's comment", goal=goal, user=user)
    api_client.force_login(another_user)
    response = api_client.patch(
        f"/goals/goal_comment/{comment.id}",
        {"text": "Shreksy!"},
        format="json"
    )

    assert response.status_code in (403, 404)


@pytest.mark.django_db
def test_reader_cannot_create_goal(api_client: APIClient, user: User, another_user: User, board: Board,
                                   category: GoalCategory) -> None:
    """Тестирует, что читатель не может создавать цели"""

    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.reader)
    api_client.force_login(another_user)
    response = api_client.post(
        "/goals/goal/create",
        {"title": "Restricted goal", "category": category.id},
        format="json"
    )
    assert response.status_code in (400, 403)


@pytest.mark.django_db
def test_reader_cannot_create_category(api_client: APIClient, user: User, another_user: User, board: Board) -> None:
    """Тестирует, что читатель не может создавать категории"""

    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.reader)

    api_client.force_login(another_user)
    response = api_client.post(
        "/goals/goal_category/create",
        {"title": "Restricted category", "board": board.id},
        format="json"
    )
    assert response.status_code in (400, 403)


@pytest.mark.django_db
def test_writer_can_create_goal(api_client: APIClient, user: User, another_user: User, board: Board,
                                category: GoalCategory) -> None:
    """Тестирует, что редактор может создавать цели"""
    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.writer)
    api_client.force_login(another_user)
    response = api_client.post(
        "/goals/goal/create",
        {"title": "Allowed goal", "category": category.id},
        format="json"
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_reader_cannot_update_goal(api_client: APIClient, user: User, another_user: User, board: Board,
                                   goal: Goal) -> None:
    """Тестирует, что читатель не может редактировать чужую цель"""

    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.reader)

    api_client.force_login(another_user)
    response = api_client.patch(
        f"/goals/goal/{goal.id}",
        {"title": "Hacked goal"},
        format="json"
    )
    assert response.status_code in (403, 404)


@pytest.mark.django_db
def test_writer_can_update_goal(api_client: APIClient, user: User, another_user: User, board: Board,
                                goal: Goal) -> None:
    """Тестирует, что редактор может редактировать цели в доске"""

    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.writer)

    api_client.force_login(another_user)
    response = api_client.patch(
        f"/goals/goal/{goal.id}",
        {"title": "Updated by writer"},
        format="json"
    )
    assert response.status_code == 200
    assert response.data["title"] == "Updated by writer"


@pytest.mark.django_db
def test_reader_cannot_delete_board(api_client: APIClient, user: User, another_user: User, board: Board) -> None:
    """Тестирует, что читатель не может удалять доску"""

    BoardParticipant.objects.create(board=board, user=another_user, role=BoardParticipant.Role.reader)
    api_client.force_login(another_user)
    response = api_client.delete(f"/goals/board/{board.id}")
    assert response.status_code in (403, 404)


@pytest.mark.django_db
def test_owner_can_delete_board(api_client: APIClient, user: User, board: Board) -> None:
    """Тестирует, что владелец может удалять доску"""

    api_client.force_login(user)
    response = api_client.delete(f"/goals/board/{board.id}")
    assert response.status_code == 204
