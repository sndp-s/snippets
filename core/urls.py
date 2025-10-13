from django.urls import path
from .views import (
    SnippetListCreateView, SnippetDetailView, SnippetDeleteView,
    TagListCreateView, TagDeleteView
)


urlpatterns = [
    path('snippets/', SnippetListCreateView.as_view(), name='snippet-list-create'),
    path('snippets/<int:pk>/', SnippetDetailView.as_view(), name='snippet-detail'),
    path('snippets/<int:pk>/delete/', SnippetDeleteView.as_view(), name='snippet-delete'),

    path('tags/', TagListCreateView.as_view(), name='tag-list-create'),
    path('tags/<int:pk>/delete/', TagDeleteView.as_view(), name='tag-delete'),
]
