from django.contrib import admin

from goals.models import GoalCategory, Goal, GoalComment, Board, BoardParticipant


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'is_deleted')
    list_filter = ('is_deleted', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20


@admin.register(BoardParticipant)
class BoardParticipantAdmin(admin.ModelAdmin):
    list_display = ('board', 'user', 'role_display', 'created_at')
    list_filter = ('role', 'board', 'created_at')
    search_fields = ('user__username', 'board__title')
    list_per_page = 20

    def role_display(self, obj):
        return obj.get_role_display()

    role_display.short_description = 'Роль'



@admin.register(GoalCategory)
class GoalCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'board', 'created_at', 'is_deleted')
    list_filter = ('is_deleted', 'board', 'created_at')
    search_fields = ('title', 'user__username', 'board__title')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'priority',
                    'deadline', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'description', 'user__username', 'category__title')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'user', 'category')
        }),
        ('Детали', {
            'fields': ('status', 'priority', 'deadline')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GoalComment)
class GoalCommentAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'user', 'goal', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('text', 'user__username', 'goal__title')
    readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20

    def short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Текст'