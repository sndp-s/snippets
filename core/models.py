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
    tags = models.ManyToManyField(
        'Tag', through='SnippetTag', related_name='snippets')
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)

    def __str__(self):
        return self.title or f"Snippet {self.id}"

    @property
    def is_root(self):
        """Return True if this snippet is a top-level stash (no parent)."""
        return self.parent is None


class SnippetTag(models.Model):
    snippet = models.ForeignKey(Snippet, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    created_dt = models.DateTimeField(auto_now_add=True)
    updated_dt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('snippet', 'tag')
