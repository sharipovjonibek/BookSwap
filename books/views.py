from __future__ import annotations

from typing import Iterable, List, Tuple
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
)

from .ai import get_ai_advice
from .forms import AIAdviceForm, BookForm, BookSearchForm, SignUpForm
from .models import Book


def _match_books(data: dict) -> Tuple[Iterable[Book], List[str], List[str]]:
    topics = [str(t).strip().lower() for t in data.get("topics", []) if str(t).strip()]
    suggestions = data.get("suggested_books", []) or []

    cond = Q()
    titles: List[str] = []
    authors: List[str] = []
    has_filters = False

    for topic in topics:
        cond |= (
            Q(title__icontains=topic)
            | Q(description__icontains=topic)
            | Q(author__icontains=topic)
        )
        has_filters = True

    for suggestion in suggestions:
        title = str(suggestion.get("title", "")).strip()
        author = str(suggestion.get("author", "")).strip()
        if title:
            cond |= Q(title__icontains=title)
            titles.append(title)
            has_filters = True
        if author:
            cond |= Q(author__icontains=author)
            authors.append(author)
            has_filters = True

    queryset = Book.objects.filter(is_active=True).select_related("owner")
    if has_filters:
        queryset = queryset.filter(cond).distinct()
    else:
        queryset = queryset.none()

    return queryset[:20], titles, authors


class BookListView(ListView):
    model = Book
    template_name = "books/book_list.html"
    context_object_name = "books"
    paginate_by = 12

    def get_queryset(self):
        queryset = Book.objects.filter(is_active=True).select_related("owner")
        queryset = queryset.order_by("-created_at")

        self.search_form = BookSearchForm(self.request.GET or None)
        self.has_filters = False

        if self.search_form.is_valid():
            data = self.search_form.cleaned_data
            query = data.get("query", "").strip()
            titles = self.search_form.parsed_titles()
            authors = self.search_form.parsed_authors()

            filters = Q()
            if query:
                filters &= (
                    Q(title__icontains=query)
                    | Q(author__icontains=query)
                    | Q(description__icontains=query)
                )
                self.has_filters = True
            if titles:
                title_q = Q()
                for title in titles:
                    title_q |= Q(title__icontains=title)
                filters &= title_q
                self.has_filters = True
            if authors:
                author_q = Q()
                for author in authors:
                    author_q |= Q(author__icontains=author)
                filters &= author_q
                self.has_filters = True

            if self.has_filters:
                queryset = queryset.filter(filters).distinct()

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = getattr(self, "search_form", BookSearchForm())
        context["has_filters"] = getattr(self, "has_filters", False)
        params = self.request.GET.copy()
        if "page" in params:
            params.pop("page")
        context["query_string"] = params.urlencode()
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "books/book_detail.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_owner"] = (
            self.request.user.is_authenticated and self.object.owner_id == self.request.user.id
        )
        return context


class OwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return obj.owner_id == self.request.user.id

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, "You do not have permission to modify this listing.")
            return redirect("books:book-detail", pk=self.get_object().pk)
        return super().handle_no_permission()


class BookCreateView(LoginRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Your book listing has been created.")
        return response

    def get_success_url(self):
        return reverse("books:book-detail", kwargs={"pk": self.object.pk})


class BookUpdateView(OwnerRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your book listing has been updated.")
        return response

    def get_success_url(self):
        return reverse("books:book-detail", kwargs={"pk": self.object.pk})


class BookDeleteView(OwnerRequiredMixin, DeleteView):
    model = Book
    template_name = "books/book_confirm_delete.html"
    success_url = reverse_lazy("books:book-list")

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "The book listing was removed.")
        return super().delete(request, *args, **kwargs)


class AIAdviceView(FormView):
    template_name = "books/ai_advice.html"
    form_class = AIAdviceForm
    success_url = reverse_lazy("books:ai-advice")

    def form_valid(self, form):
        prompt = form.cleaned_data["prompt"]
        ai_data = get_ai_advice(prompt)
        matched_books, titles, authors = _match_books(ai_data)

        if ai_data.get("_warning"):
            messages.warning(self.request, ai_data["_warning"])

        if not matched_books:
            messages.info(self.request, "We could not find exact matches, but here are some ideas to explore.")

        query_params = {}
        if titles:
            query_params["titles"] = ",".join(titles)
        if authors:
            query_params["authors"] = ",".join(authors)
        search_url = None
        if query_params:
            search_url = f"{reverse('books:book-list')}?{urlencode(query_params)}"

        context = self.get_context_data(
            form=form,
            ai_data=ai_data,
            matched_books=matched_books,
            suggested_titles=titles,
            suggested_authors=authors,
            search_url=search_url,
        )
        return self.render_to_response(context)


class SignUpView(FormView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("books:book-list")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome to BookSwap! Your account is ready.")
        return super().form_valid(form)


class BookSwapLoginView(LoginView):
    template_name = "registration/login.html"

    def form_valid(self, form):
        messages.success(self.request, "Welcome back to BookSwap!")
        return super().form_valid(form)
