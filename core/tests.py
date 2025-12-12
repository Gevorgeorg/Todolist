import pytest
from .models import User
from rest_framework.test import APIClient


@pytest.fixture
def user() -> User:
    """Создаёт тестового пользователя"""

    return User.objects.create_user(
        username="testuser",
        email="testuser@mail.ru",
        password="password123"
    )


@pytest.fixture
def api_client() -> APIClient:
    """Возвращает клиент для API-запросов"""

    return APIClient()


@pytest.mark.django_db
def test_signup(api_client: APIClient) -> None:
    """Тестирует регистрацию нового пользователя"""

    response = api_client.post(
        "/core/signup",
        {
            "username": "newuser",
            "email": "newuser@mail.ru",
            "password": "strongpass123",
            "password_repeat": "strongpass123",
            "first_name": "New",
            "last_name": "User"
        },
        format="json"
    )
    assert response.status_code == 201
    assert response.data["username"] == "newuser"
    assert "id" in response.data
    assert User.objects.filter(username="newuser").exists()


@pytest.mark.django_db
def test_login(api_client: APIClient, user: User) -> None:
    """Тестирует успешный вход в систему"""

    response = api_client.post(
        "/core/login",
        {"username": "testuser", "password": "password123"},
        format="json"
    )
    assert response.status_code == 200
    assert response.data["username"] == "testuser"


@pytest.mark.django_db
def test_login_invalid(api_client: APIClient) -> None:
    """Тестирует вход с неверными данными"""

    response = api_client.post(
        "/core/login",
        {"username": "wrong", "password": "wrong"},
        format="json"
    )
    assert response.status_code == 401
    assert "error" in response.data


@pytest.mark.django_db
def test_profile_retrieve(api_client: APIClient, user: User) -> None:
    """Тестирует получение профиля авторизованным пользователем"""

    api_client.force_login(user)
    response = api_client.get("/core/profile")
    assert response.status_code == 200
    assert response.data["username"] == "testuser"
    assert response.data["email"] == "testuser@mail.ru"


@pytest.mark.django_db
def test_profile_update(api_client: APIClient, user: User) -> None:
    """Тестирует обновление профиля"""

    api_client.force_login(user)
    response = api_client.put(
        "/core/profile",
        {
            "username": "testuser",
            "email": "testuser@mail.ru",
            "first_name": "Updated",
            "last_name": "Name"
        },
        format="json"
    )
    assert response.status_code == 200
    assert response.data["first_name"] == "Updated"


@pytest.mark.django_db
def test_profile_delete(api_client: APIClient, user: User) -> None:
    """Тестирует логаут"""

    api_client.force_login(user)
    response = api_client.delete("/core/profile")
    assert response.status_code == 204
    assert User.objects.filter(username="testuser").exists()


@pytest.mark.django_db
def test_update_password(api_client: APIClient, user: User) -> None:
    """Тестирует успешную смену пароля"""

    api_client.force_login(user)
    response = api_client.put(
        "/core/update_password",
        {
            "old_password": "password123",
            "new_password": "newpassword123"
        },
        format="json"
    )
    assert response.status_code == 200
    assert response.data["message"] == "Пароль успешно изменен"

    api_client.logout()
    login_response = api_client.post(
        "/core/login",
        {"username": "testuser", "password": "newpassword123"},
        format="json"
    )
    assert login_response.status_code == 200


@pytest.mark.django_db
def test_update_password_wrong_old(api_client: APIClient, user: User) -> None:
    """Тестирует смену пароля с неверным старым паролем"""

    api_client.force_login(user)
    response = api_client.put(
        "/core/update_password",
        {
            "old_password": "wrong",
            "new_password": "newpass"
        },
        format="json"
    )
    assert response.status_code == 400
    assert "old_password" in response.data
