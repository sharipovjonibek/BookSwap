
from django.urls import path

from .views import (
    BookListView,
    BookDetailView,
    BookCreateView,
    BookUpdateView,
    BookDeleteView,
    AIAdviceView,
)

app_name = "books"

urlpatterns = [
    path("", BookListView.as_view(), name="book-list"),
    path("books/create/", BookCreateView.as_view(), name="book-create"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book-detail"),
    path("books/<int:pk>/edit/", BookUpdateView.as_view(), name="book-update"),
    path("books/<int:pk>/delete/", BookDeleteView.as_view(), name="book-delete"),
    path("ai-advice/", AIAdviceView.as_view(), name="ai-advice"),
]
