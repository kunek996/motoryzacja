from django.conf import settings


class SecurityHeadersMiddleware:
    """Adds Content-Security-Policy and Permissions-Policy (not built into Django 5.2)."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = getattr(settings, "CONTENT_SECURITY_POLICY", "")
        self.permissions = getattr(settings, "PERMISSIONS_POLICY", "")

    def __call__(self, request):
        response = self.get_response(request)
        if self.csp:
            response.headers.setdefault("Content-Security-Policy", self.csp)
        if self.permissions:
            response.headers.setdefault("Permissions-Policy", self.permissions)
        return response
