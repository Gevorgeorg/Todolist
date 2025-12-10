from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions, filters
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination

from goals.filters import GoalFilter, GoalCommentFilter
from goals.serializers import GoalCategorySerializer, GoalSerializer, GoalCommentSerializer, BoardSerializer, \
    BoardListSerializer, BoardCreateSerializer, GoalCommentCreateSerializer
from goals.permissions import BoardPermission
from goals.models import BoardParticipant, GoalCategory, Goal, GoalComment
from django.db import models, transaction
from django_filters.rest_framework import DjangoFilterBackend

from goals.models import Status, Board, Priority


class GoalCategoryCreateView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategorySerializer


    def perform_create(self, serializer):
        # Просто сохраняем - права проверяются в validate_board сериализатора
        serializer.save(user=self.request.user)


class GoalCategoryListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategorySerializer
    pagination_class = LimitOffsetPagination


    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ["title", "created"]
    ordering = ["title"]
    search_fields = ["title"]

    def get_queryset(self):
        # Просто фильтруем по доскам где пользователь участник
        user_boards = BoardParticipant.objects.filter(
            user=self.request.user,
            board__is_deleted=False
        ).values_list('board_id', flat=True)

        return GoalCategory.objects.filter(
            board_id__in=user_boards,
            is_deleted=False
        )


class GoalCategoryView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalCategorySerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self):
        return GoalCategory.objects.filter(is_deleted=False)

    def perform_destroy(self, instance):
        Goal.objects.filter(category__board=instance.board).update(
            status=Status.archived.value
        )
        instance.is_deleted = True
        instance.save()


class GoalCreateView(CreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class GoalListView(ListAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitOffsetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = GoalFilter
    ordering_fields = ["title", "created", "due_date", "priority"]
    ordering = ["-created"]
    search_fields = ["title", "description"]

    def get_queryset(self):
        user = self.request.user

        # Если есть фильтр по категории - используем его
        category_filter = self.request.GET.get('category__in') or self.request.GET.get('category')
        if category_filter:
            # Фронтенд сам указал категории
            category_ids = [int(cid) for cid in category_filter.split(',') if cid.isdigit()]
            queryset = Goal.objects.filter(category_id__in=category_ids)
        else:
            # По умолчанию - цели всех категорий пользователя
            user_boards = BoardParticipant.objects.filter(
                user=user,
                board__is_deleted=False
            ).values_list('board_id', flat=True)

            user_categories = GoalCategory.objects.filter(
                board_id__in=user_boards,
                is_deleted=False
            ).values_list('id', flat=True)

            queryset = Goal.objects.filter(category_id__in=user_categories)

        # Дополнительная фильтрация
        queryset = queryset.filter(
            category__is_deleted=False,
            category__board__is_deleted=False
        )

        return queryset


class GoalDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self):
        return Goal.objects.all()




class GoalCommentCreateView(CreateAPIView):
    serializer_class = GoalCommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]


class GoalCommentListView(ListAPIView):
    serializer_class = GoalCommentSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]
    pagination_class = LimitOffsetPagination

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = GoalCommentFilter
    ordering_fields = ["created", "updated"]
    ordering = ["-created","updated"]  # новые комментарии сначала

    def get_queryset(self):
        """Оптимизированная версия с prefetch_related"""
        user = self.request.user

        # Используем prefetch_related для оптимизации
        queryset = GoalComment.objects.filter(
            goal__category__board__participants__user=user,
            goal__category__board__is_deleted=False,
            goal__category__is_deleted=False
        ).select_related(
            'user', 'goal', 'goal__category', 'goal__category__board'
        ).distinct()

        return queryset


class GoalCommentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalCommentSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self):
        """Все комментарии доступные пользователю"""
        user = self.request.user

        # Все комментарии в досках где пользователь участник
        return GoalComment.objects.filter(
            goal__category__board__participants__user=user,
            goal__category__board__is_deleted=False,
            goal__category__is_deleted=False
        ).select_related('user', 'goal').distinct()


class BoardView(RetrieveUpdateDestroyAPIView):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def update(self, request, *args, **kwargs):

        return super().update(request, *args, **kwargs)

    def get_queryset(self):
        return Board.objects.filter(is_deleted=False)

    def perform_destroy(self, instance: Board):
        # При удалении доски помечаем ее как is_deleted,
        # «удаляем» категории, обновляем статус целей
        with transaction.atomic():
            instance.is_deleted = True
            instance.save()
            instance.categories.update(is_deleted=True)
            Goal.objects.filter(category__board=instance).update(
                status=Status.archived.value  # или просто Status.archived
            )
        return instance


class BoardListView(ListAPIView):
    """Список досок пользователя"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardListSerializer
    pagination_class = LimitOffsetPagination


    # Добавляем фильтрацию и сортировку
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    ordering_fields = ['title', 'created']
    ordering = ['title']  # сортировка по умолчанию по названию

    def get_queryset(self):
        # Возвращаем все доски где пользователь является участником
        return Board.objects.filter(
            participants__user=self.request.user,
            is_deleted=False
        ).distinct().order_by('title')


class BoardCreateView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardCreateSerializer
