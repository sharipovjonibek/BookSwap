
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, AIAdviceView

router = DefaultRouter()
router.register(r"books", BookViewSet, basename="book")

urlpatterns = [
    path("", include(router.urls)),
    path("ai/books/advice/", AIAdviceView.as_view(), name="ai-books-advice"),
]
