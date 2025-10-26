from django.urls import path
from .views import (
    SnippetCreateView,
    SnippetUpdateView,
    SnippetDeleteView,
    SnippetDetailView,
    SnippetChildrenView,
    SnippetListView,
)

urlpatterns = [
    path('snippets/', SnippetListView.as_view(), name='snippet-list'),
    path('snippets/', SnippetCreateView.as_view(), name='snippet-create'),
    path('snippets/<int:pk>/', SnippetDetailView.as_view(), name='snippet-detail'),
    path('snippets/<int:pk>/', SnippetUpdateView.as_view(), name='snippet-update'),
    path('snippets/<int:pk>/', SnippetDeleteView.as_view(), name='snippet-delete'),
    path('snippets/<int:pk>/children/',
         SnippetChildrenView.as_view(), name='snippet-children'),
]
