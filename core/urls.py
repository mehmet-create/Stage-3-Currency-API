"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from countries.views import (
    RefreshCountriesView, CountryListView, CountryDetailView, 
    StatusView, SummaryImageView, APIRootView, CountryCreateView
)

urlpatterns = [
    path('', APIRootView.as_view()),
    path('admin/', admin.site.urls),
    path('countries/refresh', RefreshCountriesView.as_view()),
    path('countries/create', CountryCreateView.as_view(), name='country-create'),
    path('countries/image', SummaryImageView.as_view()),
    path('countries', CountryListView.as_view()),
    path('countries/<str:name>', CountryDetailView.as_view()), 
    path('status', StatusView.as_view()),
    
]