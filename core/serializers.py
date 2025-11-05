from rest_framework import serializers
from .models import Snippet, Tag


class TagSerializer(serializers.ModelSerializer):
    snippet_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Tag
        fields = ['id', 'name', 'snippet_count', 'created_dt', 'updated_dt']


class SnippetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Snippet
        fields = ['id', 'title', 'text', 'parent',
                  'tags', 'created_dt', 'updated_dt']
