import django_filters
from django.db import models
from django.db.models import QuerySet
from goals.models import Goal, GoalComment, GoalCategory


class GoalFilter(django_filters.FilterSet):

    priority = django_filters.NumberFilter(field_name='priority')
    priority__in = django_filters.BaseInFilter(field_name='priority', lookup_expr='in')

    status = django_filters.NumberFilter(field_name='status')
    status__in = django_filters.BaseInFilter(field_name='status', lookup_expr='in')

    due_date__lte = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='gte',
        input_formats=['%Y-%m-%d', '%d.%m.%Y']
    )

    due_date__gte = django_filters.DateFilter(
        field_name='due_date',
        lookup_expr='lte',
        input_formats=['%Y-%m-%d', '%d.%m.%Y']
    )

    search = django_filters.CharFilter(method='filter_search')
    board = django_filters.NumberFilter(field_name='category__board__id')

    class Meta:
        model = Goal
        fields = ['category', 'priority', 'status', 'board']

    def filter_search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.filter(
            models.Q(title__icontains=value) |
            models.Q(description__icontains=value)
        )


class GoalCommentFilter(django_filters.FilterSet):
    goal = django_filters.NumberFilter(field_name='goal__id')

    class Meta:
        model = GoalComment
        fields = ['goal']


class GoalCategoryFilter(django_filters.FilterSet):
    board = django_filters.NumberFilter(field_name='board__id')

    class Meta:
        model = GoalCategory
        fields = ['board']
