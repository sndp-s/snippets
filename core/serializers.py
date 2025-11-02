from rest_framework import serializers
from .models import Snippet, Tag


class SnippetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snippet
        fields = ['id', 'title', 'text', 'parent', 'created_dt', 'updated_dt']


class TagSerializer(serializers.ModelSerializer):
    snippet_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'snippet_count', 'created_dt', 'updated_dt']
