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


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer

    def get_queryset(self):
        return Tag.objects.annotate(
            snippet_count=models.Count('snippets')
        ).order_by('name')

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
