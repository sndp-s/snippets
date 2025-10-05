from rest_framework import serializers
from .models import Snippet, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class SnippetSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = Snippet
        fields = ['id', 'title', 'text', 'tags', 'tag_names', 'created_dt', 'updated_dt']

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        snippet = Snippet.objects.create(**validated_data)
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name=name)
            snippet.tags.add(tag)
        return snippet
