from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Q, Count
from django.db import transaction
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Snippet, Tag, SnippetTag
from .serializers import SnippetSerializer, TagSerializer


class SnippetViewSet(viewsets.ModelViewSet):
    serializer_class = SnippetSerializer
    queryset = Snippet.objects.all().order_by('-created_dt')

    def get_queryset(self):
        """
        Supports:
        - ?q=<text>              → case-insensitive search in title/text
        - ?parent=<id>           → show children of this snippet
        - ?tags=a,b,c            → include snippets with these tag names
        - ?tag_mode=any|all      → OR (default) or AND logic for tags
        - ?exclude_tags=x,y,z    → exclude snippets with these tag names
        """
        qs = super().get_queryset()
        params = self.request.query_params

        parent_id = params.get('parent')
        search = params.get('q', '').strip()
        tag_mode = params.get('tag_mode', 'any').lower()
        tags_param = params.get('tags', '')
        exclude_param = params.get('exclude_tags', '')

        # 1. Parent filter
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        else:
            qs = qs.filter(parent__isnull=True)

        # 2. Text search
        if search:
            qs = qs.filter(Q(title__icontains=search)
                           | Q(text__icontains=search))

        # 3. Include tags (case-insensitive)
        if tags_param:
            tag_names = [t.strip() for t in tags_param.split(',') if t.strip()]
            # get only tags that exist (case-insensitive)
            normalized_tag_names = [t.lower() for t in tag_names]
            existing_tags = list(
                Tag.objects.filter(name__in=normalized_tag_names)
                .values_list('name', flat=True)
            )

            if existing_tags:
                if tag_mode == 'all':
                    qs = qs.annotate(
                        match_count=Count(
                            'tags',
                            filter=Q(tags__name__in=existing_tags),
                            distinct=True
                        )
                    ).filter(match_count=len(existing_tags)).distinct()
                else:  # tag_mode = any
                    qs = qs.filter(tags__name__in=existing_tags).distinct()

        # 4. Exclude tags (case-insensitive)
        if exclude_param:
            exclude_names = [t.strip()
                             for t in exclude_param.split(',') if t.strip()]
            normalized_exclude_names = [t.lower() for t in exclude_names]
            exclude_tags = list(
                Tag.objects.filter(name__in=normalized_exclude_names)
                .values_list('name', flat=True)
            )
            if exclude_tags:
                qs = qs.exclude(tags__name__in=exclude_tags)

        return qs

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='q',
                description='Full-text search (case-insensitive) on title or text.',
                required=False,
                type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name='parent',
                description='Filter snippets by parent ID (children of given snippet).',
                required=False,
                type=OpenApiTypes.INT
            ),
            OpenApiParameter(
                name='tags',
                description='Comma-separated tag names to include (case-insensitive). Example: tags=python,tips',
                required=False,
                type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name='tag_mode',
                description='"any" (default) → snippet has ANY of tags; "all" → snippet must have ALL tags.',
                required=False,
                enum=['any', 'all'],
                type=OpenApiTypes.STR
            ),
            OpenApiParameter(
                name='exclude_tags',
                description='Comma-separated tag names to exclude (case-insensitive). Example: exclude_tags=draft,idea',
                required=False,
                type=OpenApiTypes.STR
            ),
        ],
        description="List snippets with optional full-text and tag filters.",
    )
    def list(self, request, *args, **kwargs):
        """
        GET /snippets/
        Supports text search and tag include/exclude filters.
        """
        return super().list(request, *args, **kwargs)

    @extend_schema(
        description="Create a snippet and attach tags (creating missing ones automatically)",
        request={
            "application/json": {
                "example": {
                    "title": "Python tips",
                    "text": "Use list comprehensions",
                    "tags": ["python", "tips"]
                }
            }
        }
    )
    def create(self, request, *args, **kwargs):
        tags = request.data.pop("tags", [])
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snippet = serializer.save()

        # handle tags (create if missing + attach)
        if isinstance(tags, list):
            with transaction.atomic():
                for tag_name in tags:
                    tag_name = tag_name.strip().lower()
                    if tag_name:
                        tag, _ = Tag.objects.get_or_create(name=tag_name)
                        SnippetTag.objects.get_or_create(
                            snippet=snippet, tag=tag)

        headers = self.get_success_headers(serializer.data)
        return Response(
            SnippetSerializer(snippet).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    @extend_schema(
        description="Fetch all direct child snippets of this snippet (one level deep).",
        responses={200: SnippetSerializer(many=True)},
    )
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """GET /snippets/<id>/children/"""
        try:
            snippet = Snippet.objects.get(pk=pk)
        except Snippet.DoesNotExist:
            raise NotFound("Snippet not found.")

        children = snippet.children.all().order_by('-created_dt')
        serializer = SnippetSerializer(children, many=True)
        return Response(serializer.data)

    @extend_schema(
        description="Add a tag (case-insensitive, auto-creates if missing) to this snippet.",
        request={"application/json": {"example": {"tag": "python"}}},
        responses={200: OpenApiTypes.OBJECT},
    )
    def add_tag(self, request, pk=None):
        snippet = self.get_object()
        tag_name = request.data.get("tag")

        if not tag_name:
            return Response({"error": "Tag name required"}, status=400)

        tag_name = tag_name.strip().lower()
        tag, _ = Tag.objects.get_or_create(name=tag_name)
        SnippetTag.objects.get_or_create(snippet=snippet, tag=tag)

        return Response({"message": f"Tag '{tag_name}' added."}, status=200)

    @extend_schema(
        description="Remove a tag (case-insensitive) from this snippet.",
        request={"application/json": {"example": {"tag": "python"}}},
        responses={200: OpenApiTypes.OBJECT},
    )
    def remove_tag(self, request, pk=None):
        snippet = self.get_object()
        tag_name = request.data.get("tag")

        if not tag_name:
            return Response({"error": "Tag name required"}, status=400)

        try:
            tag = Tag.objects.get(name=tag_name.strip().lower())
            SnippetTag.objects.filter(snippet=snippet, tag=tag).delete()
            return Response({"message": f"Tag '{tag_name}' removed."}, status=200)
        except Tag.DoesNotExist:
            return Response({"error": "Tag does not exist"}, status=404)

    @extend_schema(
        description="Get all tags attached to this snippet.",
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def tags(self, request, pk=None):
        snippet = self.get_object()
        tags = snippet.tags.all().values_list("name", flat=True)
        return Response({"tags": list(tags)}, status=200)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="q",
                location=OpenApiParameter.QUERY,
                description="Search tags by name",
                required=False,
                type=str,
            )
        ],
        description="List tags. Optionally filter by search query `q`"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Tag.objects.annotate(
            snippet_count=Count('snippets')
        ).order_by('name')

        search = self.request.query_params.get("q")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
            )

        return queryset

    @action(detail=True, methods=['get'])
    def snippets(self, request, pk=None):
        """
        GET /tags/<id>/snippets/
        Returns all snippets using this tag
        """
        tag = self.get_object()
        snippets = tag.snippets.all().order_by('-created_dt')
        serializer = SnippetSerializer(snippets, many=True)
        return Response(serializer.data)
