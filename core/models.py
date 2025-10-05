from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Snippet(models.Model):
    text = models.TextField()
    title = models.CharField(max_length=255, blank=True, null=True)
    tags = models.ManyToManyField('Tag', through='SnippetTag', related_name='snippets')
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title or f"Snippet {self.id}"


class SnippetTag(models.Model):
    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('snippet', 'tag')
