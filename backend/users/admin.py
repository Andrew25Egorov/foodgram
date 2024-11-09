from django.contrib import admin

from .models import Subscribe, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'id',
        'email',
        'first_name',
        'last_name',
        'password',
        'avatar',
    )
    list_filter = ('email', 'username')
    empty_value_display = '-пусто-'


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author',)
    list_editable = ('user', 'author')
