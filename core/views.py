from rest_framework import generics
from .models import Snippet, Tag
from .serializers import SnippetSerializer, TagSerializer


class SnippetListCreateView(generics.ListCreateAPIView):
    serializer_class = SnippetSerializer

    def get_queryset(self):
        queryset = Snippet.objects.all().order_by('-created_dt')
        tag_name = self.request.query_params.get('tag')
        if tag_name:
            queryset = queryset.filter(tags__name=tag_name)
        return queryset


class SnippetDeleteView(generics.DestroyAPIView):
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer


class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


class TagDeleteView(generics.DestroyAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
