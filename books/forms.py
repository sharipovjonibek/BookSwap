from __future__ import annotations

from typing import List

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Book


def _split_values(value: str) -> List[str]:
    if not value:
        return []
    parts = [chunk.strip() for chunk in value.replace(";", ",").split(",")]
    return [chunk for chunk in parts if chunk]


class StyledFormMixin:
    """Apply consistent styling to keep templates lean."""

    field_class = "form-control"

    def _apply_styles(self):
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "").strip()
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                widget.attrs["class"] = existing or "form-check-input"
            else:
                widget.attrs["class"] = f"{existing} {self.field_class}".strip()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class BookForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Book
        fields = [
            "title",
            "author",
            "description",
            "image",
            "phone_number",
            "location",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BookSearchForm(StyledFormMixin, forms.Form):
    query = forms.CharField(required=False, label="Keyword")
    titles = forms.CharField(required=False, label="Titles", help_text="Comma separated")
    authors = forms.CharField(required=False, label="Authors", help_text="Comma separated")

    def parsed_titles(self) -> List[str]:
        raw = self.cleaned_data.get("titles", "") if hasattr(self, "cleaned_data") else ""
        return _split_values(raw)

    def parsed_authors(self) -> List[str]:
        raw = self.cleaned_data.get("authors", "") if hasattr(self, "cleaned_data") else ""
        return _split_values(raw)


class AIAdviceForm(StyledFormMixin, forms.Form):
    prompt = forms.CharField(
        label="How can we help?",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Describe what kind of book you need..."}),
    )


class SignUpForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=False, help_text="Optional, helps other users reach you")

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username", "email")

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get("email", "")
        if commit:
            user.save()
        return user
