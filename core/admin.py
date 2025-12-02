from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Поля в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')
    # Поля для поиска
    search_fields = ('email', 'first_name', 'last_name', 'username')
    # Фильтры
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    # Порядок полей в форме редактирования
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),  # Сворачиваемый раздел
        }),
    )

    # Поля только для чтения
    readonly_fields = ('last_login', 'date_joined')

    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    # Сортировка
    ordering = ('username',)

    # Отображение имени в админке
    list_display_links = ('username', 'email')

    def save_model(self, request, obj, form, change):
        """Обработка сохранения пароля"""
        if form.cleaned_data.get('password'):
            # Если введен новый пароль, устанавливаем его
            obj.set_password(form.cleaned_data['password'])
        elif change and 'password' in form.changed_data:
            # Если пароль удален, не меняем его
            pass
        super().save_model(request, obj, form, change)