from rest_framework import generics, status, views
from rest_framework.response import Response
from django.db.models import Q
from rest_framework.exceptions import NotFound

from .models import Snippet
from .serializers import SnippetSerializer


class SnippetCreateView(generics.CreateAPIView):
    """
    POST /snippets/
    Create a new snippet.
    Payload:
    {
        "title": "My Note",
        "text": "Some idea",
        "parent": 5   # optional
    }
    """
    serializer_class = SnippetSerializer
    queryset = Snippet.objects.all()

    def create(self, request, *args, **kwargs):
        data = {
            "title": request.data.get("title"),
            "text": request.data.get("text"),
            "parent": request.data.get("parent")
        }
        serializer = self.get_serializer(data=data)
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


class SnippetListView(generics.ListAPIView):
    """
    GET /snippets/
    Returns all top-level snippets (those without a parent).
    Optional query param:
        ?q=<text>  → search by title or text
    """
    serializer_class = SnippetSerializer

    def get_queryset(self):
        queryset = Snippet.objects.filter(
            parent__isnull=True).order_by('-created_dt')
        search = self.request.query_params.get('q')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(text__icontains=search)
            )
        return queryset
