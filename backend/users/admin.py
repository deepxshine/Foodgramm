from django.contrib.admin import register
from django.contrib.auth.admin import UserAdmin

from .models import User


@register(User)
class UsersAdmin(UserAdmin):
    list_display = (
        'id', 'username', 'email', 'first_name', 'last_name', 'password')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('username', 'email', 'first_name', 'last_name')
