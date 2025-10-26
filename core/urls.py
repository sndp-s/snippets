from django.urls import path
from .views import (
    SnippetListCreateView,
    SnippetDetailView,
    SnippetUpdateView,
    SnippetDeleteView,
    SnippetChildrenView,
)

urlpatterns = [
    path('snippets/', SnippetListCreateView.as_view(), name='snippet-list-create'),
    path('snippets/<int:pk>/', SnippetDetailView.as_view(), name='snippet-detail'),
    path('snippets/<int:pk>/update/',
         SnippetUpdateView.as_view(), name='snippet-update'),
    path('snippets/<int:pk>/delete/',
         SnippetDeleteView.as_view(), name='snippet-delete'),
    path('snippets/<int:pk>/children/',
         SnippetChildrenView.as_view(), name='snippet-children'),
]
