from django.db import models

from core.models import User


class BaseDateTime(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")


class Board(BaseDateTime):
    title = models.CharField(max_length=255, verbose_name="Название")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалена")

    def __str__(self):
        return f"доска {self.title}"

    class Meta:
        verbose_name = "Доска"
        verbose_name_plural = "Доски"


class BoardParticipant(BaseDateTime):
    class Meta:
        unique_together = ("board", "user")
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    class Role(models.IntegerChoices):
        owner = 1, "Владелец"
        writer = 2, "Редактор"
        reader = 3, "Читатель"

    board = models.ForeignKey(
        Board,
        verbose_name="Доска",
        on_delete=models.PROTECT,
        related_name="participants",
    )
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        on_delete=models.PROTECT,
        related_name="participants",
    )
    role = models.PositiveSmallIntegerField(
        verbose_name="Роль", choices=Role.choices, default=Role.owner
    )


class Status(models.IntegerChoices):
    to_do = 1, "К выполнению"
    in_progress = 2, "В процессе"
    done = 3, "Выполнено"
    archived = 4, "Архив"


class Priority(models.IntegerChoices):
    low = 1, "Низкий"
    medium = 2, "Средний"
    high = 3, "Высокий"
    critical = 4, "Критический"


class GoalCategory(BaseDateTime):
    title = models.CharField(max_length=155, verbose_name="Название")
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Автор")
    is_deleted = models.BooleanField(default=False, verbose_name="Удалена")
    board = models.ForeignKey(Board, on_delete=models.PROTECT, related_name="categories", verbose_name="Доска")

    def __str__(self):
        return f" категория {self.title} пользователя {self.user}"

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Goal(BaseDateTime):
    title = models.CharField(max_length=155, verbose_name="Название", )
    description = models.TextField(blank=True, default="", verbose_name="Описание")
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Автор")
    category = models.ForeignKey(GoalCategory, on_delete=models.PROTECT, verbose_name="Категория")
    status = models.PositiveSmallIntegerField(
        choices=Status.choices, default=Status.to_do, verbose_name="Статус"
    )
    priority = models.PositiveSmallIntegerField(
        choices=Priority.choices, default=Priority.medium, verbose_name="Приоритет"
    )
    due_date = models.DateField(null=True, blank=True, verbose_name="Дедлайн")

    def __str__(self):
        return f"{self.title}"

    class Meta:
        verbose_name = "Цель"
        verbose_name_plural = "Цели"


class GoalComment(BaseDateTime):
    text = models.TextField(verbose_name="Текст")
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Автор")
    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='comments', verbose_name="Цель")

    def __str__(self):
        return f"Коммент от: {self.user.username}"

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
