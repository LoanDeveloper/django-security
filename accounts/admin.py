from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ("username", "email", "is_active", "is_staff")
    search_fields = ("username", "email")
    ordering = ("id",)

# Register your models here.
