from django.shortcuts import render
from goals.serializers import GoalCategorySerializer

from rest_framework.generics import CreateAPIView,ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import permissions
from rest_framework import permissions, filters
from goals.models import GoalCategory, Goal, GoalComment

import django_filters
from django.db import models
from django_filters import rest_framework




class GoalFilter(django_filters.FilterSet):
    categories = django_filters.BaseInFilter(field_name='category__id', lookup_expr='in')
    priorities = django_filters.BaseInFilter(field_name='priority', lookup_expr='in')
    statuses = django_filters.BaseInFilter(field_name='status', lookup_expr='in')
    deadline_from = django_filters.DateFilter(field_name='deadline', lookup_expr='gte')
    deadline_to = django_filters.DateFilter(field_name='deadline', lookup_expr='lte')
    # Можно добавить и эти, если хочешь точный поиск:
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')
    description = django_filters.CharFilter(field_name='description', lookup_expr='icontains')

    class Meta:
        model = Goal
        fields = []


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