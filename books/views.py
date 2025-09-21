
from typing import List
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly,AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes
)

from .models import Book
from .serializers import (
    BookSerializer,
    AIAdviceResponseSerializer,
)
from .ai import get_ai_advice

def _split_params(values) -> List[str]:
    """Accepts repeated params or comma-separated; returns cleaned list."""
    out: List[str] = []
    if not values:
        return out
    raw_list = values if isinstance(values, list) else [values]
    for v in raw_list:
        if not v:
            continue
        parts = [p.strip() for p in str(v).split(",")]
        for p in parts:
            if p:
                out.append(p)
    return out
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

@extend_schema_view(
    list=extend_schema(
        tags=["Books"],
        
        summary="List books (ads)",
        description=(
            "Public list of active ads. Filters:"
            "\n- ?q= full-text (title/author/description)"
            "\n- ?titles= (repeat or comma-separated)"
            "\n- ?authors= (repeat or comma-separated)"
        ),
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, required=False, description="Full-text query"),
            OpenApiParameter("titles", OpenApiTypes.STR, required=False, many=True, description="Title filters"),
            OpenApiParameter("authors", OpenApiTypes.STR, required=False, many=True, description="Author filters"),
        ],
        responses={200: BookSerializer(many=True)},
    ),
    create=extend_schema(tags=["Books"], summary="Create a book ad", request=BookSerializer, responses={201: BookSerializer}),
    retrieve=extend_schema(tags=["Books"], summary="Retrieve by ID", responses=BookSerializer),
    partial_update=extend_schema(tags=["Books"], summary="Update (partial)", request=BookSerializer, responses=BookSerializer),
    destroy=extend_schema(tags=["Books"], summary="Delete", responses={204: None}),
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.filter(is_active=True).select_related("owner")
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = (MultiPartParser, FormParser, JSONParser) 
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q", "").strip()
        titles = _split_params(self.request.query_params.getlist("titles"))
        authors = _split_params(self.request.query_params.getlist("authors"))

        cond = Q()
        if q:
            cond &= (Q(title__icontains=q) | Q(author__icontains=q) | Q(description__icontains=q))
        if titles:
            t_q = Q()
            for t in titles:
                t_q |= Q(title__icontains=t)
            cond &= t_q
        if authors:
            a_q = Q()
            for a in authors:
                a_q |= Q(author__icontains=a)
            cond &= a_q

        if cond:
            qs = qs.filter(cond).distinct()
        return qs

    @extend_schema(
        tags=["Books"],
        summary="Search books (same filters as list)",
        parameters=[
            OpenApiParameter("q", OpenApiTypes.STR, required=False),
            OpenApiParameter("titles", OpenApiTypes.STR, required=False, many=True),
            OpenApiParameter("authors", OpenApiTypes.STR, required=False, many=True),
        ],
        responses={200: BookSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request, *args, **kwargs):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True, context={"request": request})
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)


@extend_schema(
    tags=["AI"],
    summary="AI book advice (Gemini) → filter & results",
    description=(
        "Send a natural-language `prompt`. Returns: `ai`, `matched_books`, and `filter_query`"
        " for frontend redirect to `/api/books/?titles=...&authors=...`."
    ),
    parameters=[
        OpenApiParameter("prompt", OpenApiTypes.STR, location=OpenApiParameter.QUERY, required=False,
                         description="User problem/goal; use body in POST for JSON."),
    ],
    responses={200: AIAdviceResponseSerializer},
)
class AIAdviceView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _match(self, data):
        topics = [t.lower() for t in data.get("topics", [])]
        suggestions = data.get("suggested_books", [])

        q_objects = Q()
        titles: List[str] = []
        authors: List[str] = []

        for t in topics:
            q_objects |= Q(title__icontains=t) | Q(description__icontains=t) | Q(author__icontains=t)
        for s in suggestions:
            title = (s.get("title") or "").strip()
            author = (s.get("author") or "").strip()
            if title:
                q_objects |= Q(title__icontains=title)
                titles.append(title)
            if author:
                q_objects |= Q(author__icontains=author)
                authors.append(author)

        matched = Book.objects.filter(is_active=True).filter(q_objects).distinct()[:50]
        return matched, titles, authors

    def _respond(self, prompt: str):
        if not prompt:
            return Response({"detail": "Provide a 'prompt' in query (?prompt=) or POST JSON body."}, status=400)
        data = get_ai_advice(prompt)
        matched, titles, authors = self._match(data)
        ser = BookSerializer(matched, many=True, context={"request": None})
        return Response({"ai": data, "matched_books": ser.data, "filter_query": {"titles": titles, "authors": authors}})

    def get(self, request, *args, **kwargs):
        prompt = request.query_params.get("prompt", "").strip()
        return self._respond(prompt)

    def post(self, request, *args, **kwargs):
        prompt = (request.data or {}).get("prompt", "").strip()
        return self._respond(prompt)


class HealthView(APIView):
    """Simple health-check endpoint for deployment sanity."""
    authentication_classes = []
    permission_classes = []

    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"})
