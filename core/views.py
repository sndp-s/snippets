from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.exceptions import NotFound

from .models import Snippet, Tag
from .serializers import SnippetSerializer, TagSerializer


class SnippetViewSet(viewsets.ModelViewSet):
    """
    Supports:
    - GET /snippets/  (list)
    - POST /snippets/  (create)
    - GET /snippets/<id>/  (retrieve)
    - PATCH /snippets/<id>/  (update)
    - DELETE /snippets/<id>/ (delete)
    - GET /snippets/<id>/children/ (custom children endpoint)
    """
    serializer_class = SnippetSerializer
    queryset = Snippet.objects.all().order_by('-created_dt')

    def get_queryset(self):
        queryset = super().get_queryset()
        parent_id = self.request.query_params.get('parent')
        search = self.request.query_params.get('q')

        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            queryset = queryset.filter(parent__isnull=True)

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(text__icontains=search)
            )

        return queryset.distinct()

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

    @action(detail=True, methods=["post"])
    def add_tag(self, request, pk=None):
        snippet = self.get_object()
        tag_name = request.data.get("tag")

        if not tag_name:
            return Response({"error": "Tag name required"}, status=400)

        tag, _ = Tag.objects.get_or_create(name=tag_name)
        SnippetTag.objects.get_or_create(snippet=snippet, tag=tag)

        return Response({"message": f"Tag '{tag_name}' added."}, status=200)

    @action(detail=True, methods=["post"])
    def remove_tag(self, request, pk=None):
        snippet = self.get_object()
        tag_name = request.data.get("tag")

        if not tag_name:
            return Response({"error": "Tag name required"}, status=400)

        try:
            tag = Tag.objects.get(name=tag_name)
            SnippetTag.objects.filter(snippet=snippet, tag=tag).delete()
            return Response({"message": f"Tag '{tag_name}' removed."}, status=200)
        except Tag.DoesNotExist:
            return Response({"error": "Tag does not exist"}, status=404)

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
