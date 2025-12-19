from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    list_filter = ('is_staff', 'is_active', 'is_superuser')

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    ordering = ('username',)

    list_display_links = ('username', 'email')

    def save_model(self, request, obj, form, change):
        """Обработка сохранения пароля"""

        if form.cleaned_data.get('password'):
            obj.set_password(form.cleaned_data['password'])
        elif change and 'password' in form.changed_data:
            pass
        super().save_model(request, obj, form, change)
