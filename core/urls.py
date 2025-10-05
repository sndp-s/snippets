from django.urls import path
from .views import (
    SnippetListCreateView, SnippetDeleteView,
    TagListCreateView, TagDeleteView
)

urlpatterns = [
    path('snippets/', SnippetListCreateView.as_view(), name='snippet-list-create'),
    path('snippets/<int:pk>/', SnippetDeleteView.as_view(), name='snippet-delete'),
    path('tags/', TagListCreateView.as_view(), name='tag-list-create'),
    path('tags/<int:pk>/', TagDeleteView.as_view(), name='tag-delete'),
]
