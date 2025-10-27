from django.http import JsonResponse

class ExternalApiError(Exception):
    def __init__(self, api_name, message="External data source unavailable"):
        self.api_name = api_name
        self.message = message
        super().__init__(self.message)

    def to_response(self):
        return JsonResponse(
            {
                "error": self.message,
                "details": f"Could not fetch data from {self.api_name}"
            },
            status=503
        )

# Custom exception for 400 Validation Errors
class ValidationError(Exception):
    def __init__(self, details, message="Validation failed"):
        self.message = message
        self.details = details
        super().__init__(self.message)

    def to_response(self):
        return JsonResponse(
            {
                "error": self.message,
                "details": self.details
            },
            status=400
        )