from rest_framework import generics
from django.db.models import Q
from .models import Snippet, Tag
from rest_framework.exceptions import ValidationError
from .serializers import SnippetSerializer, TagSerializer


class SnippetListCreateView(generics.ListCreateAPIView):
    serializer_class = SnippetSerializer

    def get_queryset(self):
        queryset = Snippet.objects.all().order_by('-created_dt')

        tag_name = self.request.query_params.get('tag')
        search = self.request.query_params.get('q')

        if tag_name:
            queryset = queryset.filter(tags__name__icontains=tag_name)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(text__icontains=search))

        return queryset.distinct()


class SnippetDetailView(generics.RetrieveUpdateAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer


class SnippetDeleteView(generics.DestroyAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer


class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


# TODO prevent tag deletion if it is associated with a snippet
class TagDeleteView(generics.DestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def perform_destroy(self, instance):
        # Check if this tag is used by any snippets
        if instance.snippets.exists():
            raise ValidationError(
                {"detail": f"Tag '{instance.name}' cannot be deleted because it is associated with one or more snippets."}
            )
        instance.delete()
