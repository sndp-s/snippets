from rest_framework import generics, status, views
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.exceptions import NotFound

from .models import Snippet
from .serializers import SnippetSerializer


class SnippetListCreateView(generics.ListCreateAPIView):
    """
    GET → list top-level snippets
    POST → create new snippet (with or without parent)
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
                Q(title__icontains=search) | Q(text__icontains=search)
            )
        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        snippet = serializer.save()
        return Response(self.get_serializer(snippet).data, status=status.HTTP_201_CREATED)


class SnippetUpdateView(generics.UpdateAPIView):
    """
    PATCH /snippets/<id>/
    Update snippet title, text, or parent.
    """
    serializer_class = SnippetSerializer
    queryset = Snippet.objects.all()

    def update(self, request, *args, **kwargs):
        snippet = self.get_object()
        serializer = self.get_serializer(
            snippet, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = serializer.save()
        return Response(self.get_serializer(updated).data)


class SnippetDeleteView(generics.DestroyAPIView):
    """
    DELETE /snippets/<id>/
    Deletes snippet and cascades its children.
    """
    serializer_class = SnippetSerializer
    queryset = Snippet.objects.all()


class SnippetDetailView(generics.RetrieveAPIView):
    """
    GET /snippets/<id>/
    Get snippet details by ID.
    """
    serializer_class = SnippetSerializer
    queryset = Snippet.objects.all()


class SnippetChildrenView(views.APIView):
    """
    GET /snippets/<id>/children/
    Returns all direct children of the snippet.
    """

    def get(self, request, pk):
        try:
            snippet = Snippet.objects.get(pk=pk)
        except Snippet.DoesNotExist:
            raise NotFound("Snippet not found.")

        children = snippet.children.all().order_by('-created_dt')
        serializer = SnippetSerializer(children, many=True)
        return Response(serializer.data)
