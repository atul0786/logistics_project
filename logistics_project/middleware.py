
from django.http import HttpResponseBadRequest
from django.core.exceptions import DisallowedHost

class FixHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Validate host
            host = request.get_host()
            
            # Allow these hosts
            allowed_hosts = [
                'goodwayexpress.online',
                'www.goodwayexpress.online',
                '147.93.110.231',
                'localhost',
                '127.0.0.1',
                '0.0.0.0',
            ]
            
            # Check if host is allowed
            if any(allowed in host for allowed in allowed_hosts):
                return self.get_response(request)
            else:
                return HttpResponseBadRequest("Invalid host header")
                
        except DisallowedHost:
            # If host is invalid, set a default and continue
            request.META['HTTP_HOST'] = 'goodwayexpress.online'
            return self.get_response(request)
