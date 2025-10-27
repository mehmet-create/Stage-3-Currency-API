from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.exceptions import NotFound
from django.http import JsonResponse, FileResponse
from django.conf import settings
import os
from .models import Country, Status
from .serializers import CountrySerializer, StatusSerializer
from .services import refresh_country_data 
from .exceptions import ExternalApiError 
from .serializers import CountrySerializer, StatusSerializer
from rest_framework import status
from datetime import datetime
# --- POST /countries/refresh ---
class APIRootView(APIView):
    """Provides a simple welcome message for the API root."""
    def get(self, request):
        return Response({
            "message": "Welcome to the Country Currency & Exchange API.",
            "available_endpoints": [
                "/countries",
                "/countries/refresh (POST)",
                "/countries/image",
                "/status"
            ]
        })
class RefreshCountriesView(APIView):
    def post(self, request):
        try:
            updated_count, current_time = refresh_country_data()
            
            response_data = StatusSerializer({
                'total_countries': updated_count, 
                'last_refreshed_at': current_time
            }).data
            
            return Response(response_data, status=200)

        except ExternalApiError as e:
            return e.to_response()
        except Exception:
            return JsonResponse({"error": "Internal server error"}, status=500)
class CountryCreateView(APIView):
    def post(self, request):
        serializer = CountrySerializer(data=request.data)
        
        if serializer.is_valid():
            # Pass the server-controlled fields to the .save() method
            # This is necessary because they were marked read_only 
            # and were not in the request data.
            country = serializer.save(
                last_refreshed_at=datetime.now(),
                # You would also calculate and set estimated_gdp and exchange_rate here
                # For simplicity, we'll only set the timestamp for now.
            )
            return Response(CountrySerializer(country).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# --- GET /countries ---
class CountryListView(generics.ListAPIView):
    serializer_class = CountrySerializer
    
    def get_queryset(self):
        queryset = Country.objects.all()
        
        # Filtering (case-insensitive)
        region = self.request.query_params.get('region')
        currency = self.request.query_params.get('currency')
        
        if region:
            queryset = queryset.filter(region__iexact=region)
        if currency:
            queryset = queryset.filter(currency_code__iexact=currency)
            
        # Sorting
        sort_param = self.request.query_params.get('sort')
        if sort_param:
            order_by_field = {
                'gdp_desc': '-estimated_gdp',
                'gdp_asc': 'estimated_gdp',
                'name_asc': 'name',
                'name_desc': '-name',
                'population_desc': '-population',
            }.get(sort_param.lower())
            
            if order_by_field:
                queryset = queryset.order_by(order_by_field)

        return queryset

# --- GET /countries/:name & DELETE /countries/:name ---
class CountryDetailView(generics.RetrieveDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    lookup_field = 'name' # Use 'name' from the URL path
    
    def get_object(self):
        # Case-insensitive lookup for :name
        name = self.kwargs.get('name')
        try:
            # Use name__iexact for case-insensitive matching
            return self.queryset.get(name__iexact=name)
        except Country.DoesNotExist:
            # Return required 404 response
            raise NotFound(detail={"error": "Country not found"})

    def destroy(self, request, *args, **kwargs):
        # Handles the deletion and ensures 404 is returned if not found via get_object
        instance = self.get_object() 
        self.perform_destroy(instance)
        return Response(status=204) # 204 No Content on success

# --- GET /status ---
class StatusView(APIView):
    def get(self, request):
        try:
            status = Status.objects.get(pk=1)
            return Response(StatusSerializer(status).data, status=200)
        except Status.DoesNotExist:
            # Return default status if refresh has never run
            return Response({
                "total_countries": 0, 
                "last_refreshed_at": None
            }, status=200)

# --- GET /countries/image ---
class SummaryImageView(APIView):
    def get(self, request):
        image_path = os.path.join('cache', 'summary.png')

        if os.path.exists(image_path):
            return FileResponse(open(image_path, 'rb'), content_type='image/png')
        else:
            # Return 200 OK with JSON error body as specified
            return JsonResponse({ "error": "Summary image not found" }, status=200)