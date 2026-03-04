from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'student_id', 'college', 'role', 'is_verified', 'is_active']
    list_filter = ['role', 'is_verified', 'is_active', 'college']
    search_fields = ['username', 'email', 'student_id']
