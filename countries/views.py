from django.shortcuts import render
import os
from pathlib import Path
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from django.http import FileResponse
from .models import Country, AppStatus
from .serializers import CountrySerializer, StatusSerializer
from .services import refresh_all_data
# Create your views here.

# --- Custom Exception Handler for 503 ---
class ExternalServiceUnavailable(Exception):
    pass
    
# --- Custom ViewSet for the refresh endpoint ---
class RefreshViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Handles the POST /countries/refresh endpoint."""
    

    @action(detail=False, methods=['post'])
    def refresh(self, request):
        try:
            # Check if refresh_all_data is correctly imported (it is, from .services)
            total_countries = refresh_all_data() 
            
            # If the service call succeeds, return the success message
            return Response({
                "message": "Cache successfully refreshed", 
                "total_countries": total_countries
            }, status=status.HTTP_200_OK)
                
        except Exception as e:
            # --- CRITICAL ERROR TRAPPING ---
            # This will catch ANY error and print its details
            print("\n--- CRITICAL REFRESH ERROR ---\n")
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Details: {e}")
            print("\n------------------------------\n")
            
            # If you were trying to handle a 503 error, that code goes here...
            if str(e).startswith("Could not fetch data from"):
                return Response({
                    "error": "External data source unavailable",
                    "details": str(e)
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            # For any other uncaught error, return a 500
            return Response({
                "error": "Internal server error during refresh. Check server logs.",
                "details": str(e) # Exposing 'e' helps debug in Postman
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Core Country ViewSet ---
class CountryViewSet(viewsets.ModelViewSet):
    """
    Handles GET /countries, GET /countries/:name, DELETE /countries/:name.
    PUT/PATCH are implicitly handled by ModelViewSet but can be disabled.
    """
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    lookup_field = 'name' # Use name for detail lookup
    
    # Custom queryset to handle filters and sorting
    def get_queryset(self):
        queryset = self.queryset
        
        # 1. Filtering
        region = self.request.query_params.get('region')
        currency = self.request.query_params.get('currency')
        
        if region:
            queryset = queryset.filter(region__iexact=region)
        if currency:
            queryset = queryset.filter(currency_code__iexact=currency)

        # 2. Sorting
        sort_by = self.request.query_params.get('sort')
        if sort_by == 'gdp_desc':
            # -estimated_gdp sorts by descending, nulls last
            queryset = queryset.order_by('-estimated_gdp') 
        elif sort_by == 'gdp_asc':
            queryset = queryset.order_by('estimated_gdp')
        
        return queryset

    # Override destroy to ensure case-insensitive lookup for DELETE
    def destroy(self, request, *args, **kwargs):
        name = kwargs.get(self.lookup_field)
        try:
            instance = self.get_queryset().get(Q(name__iexact=name)) 
        except Country.DoesNotExist:
            return Response({"error": "Country not found"}, status=status.HTTP_404_NOT_FOUND)
            
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

# --- Status and Image ViewSet ---
class StatusImageViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Handles GET /status and GET /countries/image."""
    queryset = AppStatus.objects.all()
    serializer_class = StatusSerializer
    # GET /status
    @action(detail=False, methods=['get'])
    def status(self, request):
        try:
            status_obj = AppStatus.objects.get(pk=1)
            serializer = StatusSerializer(status_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AppStatus.DoesNotExist:
            return Response({
                "total_countries": 0, 
                "last_refreshed_at": None
            }, status=status.HTTP_200_OK)

    # GET /countries/image
    @action(detail=False, methods=['get'], url_path='image')
    def summary_image(self, request):
        image_path = Path("cache") / "summary.png"
        
        if not image_path.exists():
            return Response({
                "error": "Summary image not found"
            }, status=status.HTTP_200_OK) # Return 200 as per spec
        
        # Serve the image file
        response = FileResponse(open(image_path, 'rb'), content_type='image/png')
        response['Content-Disposition'] = 'attachment; filename="summary.png"'
        return response