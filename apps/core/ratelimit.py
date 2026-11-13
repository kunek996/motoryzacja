"""Small cache-based rate limiter (no extra dependency).

Use a shared cache (Redis) in production so limits apply across all workers.
"""
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render


def client_ip(request) -> str:
    """REMOTE_ADDR, or the address added by our own reverse proxies (RATELIMIT_PROXY_COUNT)."""
    proxies = getattr(settings, "RATELIMIT_PROXY_COUNT", 0)
    if proxies:
        chain = [p.strip() for p in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",") if p.strip()]
        if len(chain) >= proxies:
            return chain[-proxies]
    return request.META.get("REMOTE_ADDR", "unknown")


def incr(key: str, period: int) -> int:
    """Increment a counter that expires `period` seconds after its first hit; return the new value."""
    full = f"rl:{key}"
    if cache.add(full, 1, period):
        return 1
    try:
        return cache.incr(full)
    except ValueError:  # expired between add and incr
        cache.add(full, 1, period)
        return 1


def count(key: str) -> int:
    return cache.get(f"rl:{key}", 0)


def reset(key: str) -> None:
    cache.delete(f"rl:{key}")


def hit(key: str, limit: int, period: int) -> bool:
    """Count one hit; return True while the caller is within `limit` hits per `period` seconds."""
    return incr(key, period) <= limit


def ratelimit(group: str, limit: int, period: int, by: str = "ip", methods=("POST",)):
    """Decorator. `by` = 'ip' or 'user' (falls back to IP for anonymous users)."""

    def deco(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            if getattr(settings, "RATELIMIT_ENABLED", True) and request.method in methods:
                if by == "user" and request.user.is_authenticated:
                    ident = f"u{request.user.pk}"
                else:
                    ident = client_ip(request)
                if not hit(f"{group}:{ident}", limit, period):
                    return render(request, "429.html", status=429)
            return view(request, *args, **kwargs)

        return wrapper

    return deco
