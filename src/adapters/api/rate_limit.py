"""API rate limiting via slowapi."""

from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.infrastructure.config import Settings

limiter = Limiter(key_func=get_remote_address, enabled=False)


def rate_limit_string(settings: Settings) -> str:
    """Build slowapi limit expression from settings (e.g. 10/60second)."""
    return f"{settings.rate_limit_requests}/{settings.rate_limit_window_seconds}second"


def register_rate_limiting(app, settings: Settings) -> None:
    """Attach slowapi limiter to the FastAPI app."""
    limiter.enabled = settings.rate_limit_enabled
    app.state.limiter = limiter
    app.state.rate_limit = rate_limit_string(settings)
    if settings.rate_limit_enabled:
        app.add_middleware(SlowAPIMiddleware)
