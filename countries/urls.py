from django.urls import path
from django.views.generic import RedirectView
from .views import (
    CountryViewSet, 
    RefreshViewSet, 
    StatusImageViewSet
)

urlpatterns = [
    path(
        '', 
        RedirectView.as_view(pattern_name='country-list', permanent=False), 
        name='api-root'
    ),
    path(
        'countries/refresh/', 
        RefreshViewSet.as_view({'post': 'refresh'}), 
        name='country-refresh'
    ),
    path(
        'status-image/status/', 
        StatusImageViewSet.as_view({'get': 'status'}), 
        name='status-image-status'
    ),
    path(
        'countries/image/', 
        StatusImageViewSet.as_view({'get': 'summary_image'}), 
        name='countries-image'
    ),
    path(
        'countries/', 
        CountryViewSet.as_view({'get': 'list', 'post': 'create'}), 
        name='country-list'
    ),
    path(
        'countries/<str:name>/', 
        CountryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
        name='country-detail'
    ),
]