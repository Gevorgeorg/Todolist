from django.db.models import QuerySet
import sys
import time
from datetime import datetime
from django.core.management.base import BaseCommand
from core.models import User
from goals.models import Goal, GoalCategory, BoardParticipant, Status
from tgbot.models import TgUser
from tgbot.tg.client import TgClient


class Command(BaseCommand):

    def __init__(self) -> None:
        super().__init__()
        self.user_states: dict = {}  # ключ — chat_id

    def handle(self, *args, **kwargs) -> None:
        """Основной цикл опроса Telegram API на наличие новых сообщений."""

        client = TgClient()
        self.stdout.write("Бот запущен")
        offset = 0
        while True:
            try:
                response = client.get_updates(offset=offset, timeout=10)
                if response.ok and response.result:
                    for update in response.result:
                        offset = update.update_id + 1
                        if update.message and update.message.text:
                            tg_message = update.message
                            reply = self._process_message(
                                chat_id=tg_message.chat.id,
                                username=tg_message.from_.username or "",
                                text=tg_message.text.strip()
                            )
                            client.send_message(tg_message.chat.id, reply)
                time.sleep(0.1)
            except KeyboardInterrupt:
                self.stdout.write("\nБот остановлен")
                sys.exit(0)
            except Exception as e:
                self.stdout.write(f"Ошибка: {e}")
                time.sleep(5)

    def _process_message(self, chat_id: int, username: str, text: str) -> str:
        """Основной обработчик входящего сообщения от пользователя"""

        if text.lower() == '/cancel':
            self.user_states.pop(chat_id, None)
            return "Действие отменено!"

        tg_user, _ = TgUser.objects.get_or_create(
            telegram_chat_id=chat_id,
            defaults={'username': username}
        )

        if not tg_user.user:
            if not tg_user.verification_code:
                tg_user.generate_verification_code()
            return (
                f"Код верификации: {tg_user.verification_code}\n"
                "Введите его в личном кабинете на сайте, чтобы привязать аккаунт."
            )

        command = text.lower()
        if command == '/goals':
            return self._get_goals(tg_user.user)
        if command == '/create':
            return self._initiate_goal_creation(chat_id, tg_user.user)

        if chat_id in self.user_states:
            return self._handle_goal_creation_step(chat_id, tg_user, text)

        return (
            "Доступные команды:\n\n"
            "/goals — показать активные цели\n"
            "/create — создать новую цель\n"
            "/cancel — отменить текущее действие"
        )

    def _get_goals(self, user: User) -> str:
        """Возвращает список активных целей пользователя"""

        goals: QuerySet = Goal.objects.filter(
            user=user,
            status__in=[Status.to_do, Status.in_progress]
        ).select_related('category').order_by('-created')

        if not goals:
            return "У вас нет активных целей."

        lines = ["Ваши цели:"]
        for goal in goals:
            description = f"{goal.description[:50]}..." if goal.description else ""
            deadline = f"{goal.due_date.strftime('%d.%m.%Y')}" if goal.due_date else ""
            category_title = goal.category.title if goal.category else "Без категории"
            lines.append(f"**{goal.title}**\n{description}\nдо: {deadline}\nкатегория: {category_title}")
        return "\n\n".join(lines)

    def _initiate_goal_creation(self, chat_id: int, user: User) -> str:
        """Начинает процесс создания цели: проверяет наличие категорий и предлагает выбор."""

        participant_board_ids = BoardParticipant.objects.filter(user=user).values_list('board_id', flat=True)
        all_categories = list(GoalCategory.objects.filter(
            board_id__in=participant_board_ids,
            is_deleted=False
        ))

        if not all_categories:
            return "У вас нет категорий. Создайте категорию на сайте."

        categories = "\n".join(f"{i + 1}. {cat.title}" for i, cat in enumerate(all_categories))
        self.user_states[chat_id] = {'step': 'category', 'categories': all_categories}
        return f"Выберите номер категории:\n{categories}"

    def _handle_goal_creation_step(self, chat_id: int, tg_user: TgUser, user_input: str) -> str:
        """Обрабатывает текущий этап создания цели в зависимости от состояния пользователя"""

        state = self.user_states.get(chat_id)
        if not state:
            return "Состояние утеряно. Начните с /create."

        step = state.get('step')

        if step == 'category':
            try:
                choice_index = int(user_input) - 1
                available_categories = state.get('categories')
                if 0 <= choice_index < len(available_categories):
                    selected_category = available_categories[choice_index]
                    self.user_states[chat_id] = {
                        'step': 'title',
                        'category_id': selected_category.id,
                        'category_title': selected_category.title
                    }
                    return f"Категория: {selected_category.title}\nВведите название цели:"
                return "Неверный номер."
            except ValueError:
                return "Введите число."

        if step == 'title':
            if len(user_input) > 155:
                return "Название слишком длинное (макс. 155 символов)."
            self.user_states[chat_id] = {
                'step': 'description',
                'category_id': state['category_id'],
                'category_title': state['category_title'],
                'title': user_input
            }
            return "Введите описание (или 'нет'):"

        if step == 'description':
            desc = "" if user_input.lower() in ('нет', 'no', '') else user_input
            self.user_states[chat_id] = {
                'step': 'due_date',
                'category_id': state['category_id'],
                'category_title': state['category_title'],
                'title': state['title'],
                'description': desc
            }
            return "Дедлайн ДД.ММ.ГГГГ (или 'нет'):"

        if step == 'due_date':
            due_date = None
            if user_input.lower() not in ('нет', 'no', ''):
                try:
                    due_date = datetime.strptime(user_input.strip(), '%d.%m.%Y').date()
                except ValueError:
                    return "Формат: 25.12.2025"

            category = GoalCategory.objects.filter(
                id=state['category_id'],
                is_deleted=False
            ).first()
            if not category:
                self.user_states.pop(chat_id, None)
                return "Категория не найдена. Начните заново."

            Goal.objects.create(
                title=state['title'],
                description=state.get('description', ''),
                user=tg_user.user,
                category=category,
                status=Status.to_do,
                due_date=due_date
            )

            self.user_states.pop(chat_id, None)
            return f"Цель создана!\n{state['title']}\nКатегория: {state['category_title']}"

        return "Ошибка состояния. Используйте /cancel."
