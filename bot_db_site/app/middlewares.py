from django.http import HttpResponseForbidden


class AllowedIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_ips = ['allowed.host..']

    def __call__(self, request):
        client_ip = self.get_client_ip(request)
        
        if client_ip not in self.allowed_ips:
            return HttpResponseForbidden("Access denied.")
        
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
