
from django.contrib import admin
from .models import Book

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id","title","owner","author","phone_number","is_active","created_at")
    search_fields = ("title","author","description","owner__username")
    list_filter = ("is_active","created_at")
