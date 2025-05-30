from django.http import JsonResponse
from django.conf import settings

class IPAddressCheckerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.protected_prefix = "/admin/"

    def __call__(self, request):
        if request.path.startswith(self.protected_prefix):
            ip_address = self.get_client_ip(request)

            # Si la dirección IP no está en la lista mostrará una página de error
            if ip_address not in settings.ALLOWED_IPS:
                return JsonResponse({"error":"Acceso restringido. Tu IP no está permitida."}, status=403)
            return self.get_response(request)
        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded.split(",")[0] if x_forwarded else request.META.get("REMOTE_ADDR")
