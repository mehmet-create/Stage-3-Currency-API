# project_name/urls.py
from django.urls import path
from countries.views import (
    RefreshCountriesView, CountryListView, CountryDetailView, 
    StatusView, SummaryImageView
)

urlpatterns = [
    # API Endpoints
    path('countries/refresh', RefreshCountriesView.as_view()),
    path('countries/image', SummaryImageView.as_view()),
    path('countries', CountryListView.as_view()),
    path('countries/<str:name>', CountryDetailView.as_view()), 
    path('status', StatusView.as_view()),
    # Include admin or other paths as needed
]