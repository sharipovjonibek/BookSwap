
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from books.views import SignUpView, BookSwapLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", BookSwapLoginView.as_view(), name="login"),
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("books.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
