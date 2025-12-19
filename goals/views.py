from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, filters
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.generics import (CreateAPIView,
                                     ListAPIView,
                                     RetrieveUpdateDestroyAPIView)
from goals.serializers import (GoalCategorySerializer,
                               GoalSerializer,
                               GoalCommentSerializer,
                               GoalCommentCreateSerializer,
                               BoardSerializer,
                               BoardListSerializer,
                               BoardCreateSerializer)
from goals.models import Board, BoardParticipant, Goal, GoalCategory, GoalComment, Status
from goals.permissions import BoardPermission
from goals.filters import GoalFilter, GoalCommentFilter, GoalCategoryFilter
from core.models import User


def get_user_board_ids(user: User) -> list:
    """Возвращает ID досок, где пользователь является участником и доска не удалена"""

    return list(BoardParticipant.objects.filter(
        user=user,
        board__is_deleted=False
    ).values_list('board_id', flat=True))


class GoalCategoryCreateView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategorySerializer


class GoalCategoryListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = GoalCategorySerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = GoalCategoryFilter
    ordering_fields = ["title", "created"]
    ordering = ["title"]
    search_fields = ["title"]

    def get_queryset(self) -> QuerySet:
        board_ids: list = get_user_board_ids(self.request.user)
        return GoalCategory.objects.filter(
            board_id__in=board_ids,
            is_deleted=False)


class GoalCategoryView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalCategorySerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self) -> QuerySet:
        return GoalCategory.objects.filter(is_deleted=False)

    def perform_destroy(self, instance: GoalCategory) -> None:
        Goal.objects.filter(category=instance).update(status=Status.archived)
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])


class GoalCreateView(CreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]


class GoalListView(ListAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = GoalFilter
    ordering_fields = ["title", "created", "due_date", "priority"]
    ordering = ["-created"]
    search_fields = ["title", "description"]

    def get_queryset(self) -> QuerySet:
        user: User = self.request.user
        category_filter = self.request.GET.get('category__in') or self.request.GET.get('category')

        if category_filter:
            try:
                category_ids = [int(cid) for cid in category_filter.split(',') if cid.isdigit()]
                queryset = Goal.objects.filter(category_id__in=category_ids)
            except ValueError:
                queryset = Goal.objects.none()
        else:
            board_ids: list = get_user_board_ids(user)
            category_ids = GoalCategory.objects.filter(
                board_id__in=board_ids,
                is_deleted=False
            ).values_list('id', flat=True)
            queryset: QuerySet = Goal.objects.filter(category_id__in=category_ids)

        return queryset.filter(category__is_deleted=False,
                               category__board__is_deleted=False
                               ).select_related('user', 'category', 'category__board')


class GoalDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self) -> QuerySet:
        return Goal.objects.all()

    def perform_destroy(self, instance):
        instance.status = Status.archived
        instance.save(update_fields=['status'])


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
    ordering = ["-created"]

    def get_queryset(self) -> QuerySet:
        user: User = self.request.user
        return GoalComment.objects.filter(
            goal__category__board__participants__user=user,
            goal__category__board__is_deleted=False,
            goal__category__is_deleted=False
        ).select_related(
            'user', 'goal', 'goal__category'
        ).distinct()


class GoalCommentDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalCommentSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self) -> QuerySet:
        user: User = self.request.user
        return GoalComment.objects.filter(
            goal__category__board__participants__user=user,
            goal__category__board__is_deleted=False,
            goal__category__is_deleted=False
        ).select_related('user', 'goal').distinct()


class BoardView(RetrieveUpdateDestroyAPIView):
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, BoardPermission]

    def get_queryset(self) -> QuerySet:
        return Board.objects.filter(is_deleted=False)

    def perform_destroy(self, instance: Board) -> Board:
        instance.is_deleted = True
        instance.save(update_fields=['is_deleted'])
        instance.categories.update(is_deleted=True)
        Goal.objects.filter(category__board=instance).update(status=Status.archived)
        return instance


class BoardListView(ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardListSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['title', 'created']
    ordering = ['title']

    def get_queryset(self) -> QuerySet:
        return Board.objects.filter(
            participants__user=self.request.user,
            is_deleted=False
        ).distinct()


class BoardCreateView(CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BoardCreateSerializer
