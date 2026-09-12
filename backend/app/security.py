from __future__ import annotations

import hmac
import threading
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


PUBLIC_PATHS = {"/api/health", "/api/ready", "/docs", "/openapi.json"}


def valid_api_key(provided: str | None, expected: str | None) -> bool:
    return bool(provided and expected and hmac.compare_digest(provided, expected))


class ProductionSecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, production: bool, api_key: str | None, requests_per_minute: int):
        super().__init__(app)
        self.production = production
        self.api_key = api_key
        self.limit = max(1, requests_per_minute)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    async def dispatch(self, request: Request, call_next):
        if not self.production or request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        provided = request.headers.get("x-api-key")
        if not valid_api_key(provided, self.api_key):
            return JSONResponse({"detail": "Valid API key required"}, status_code=401)
        now = time.monotonic()
        identity = hmac.new(self.api_key.encode(), provided.encode(), "sha256").hexdigest()
        with self._lock:
            bucket = self._requests[identity]
            while bucket and bucket[0] <= now - 60:
                bucket.popleft()
            if len(bucket) >= self.limit:
                return JSONResponse({"detail": "Request rate limit exceeded"}, status_code=429, headers={"Retry-After": "60"})
            bucket.append(now)
        return await call_next(request)
