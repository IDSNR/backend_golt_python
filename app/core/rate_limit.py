from collections import defaultdict, deque
from time import monotonic

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 60, window_seconds: int = 60) -> None:
        super().__init__(app)
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.method == 'OPTIONS' or request.url.path in {'/health', '/health/database'}:
            return await call_next(request)

        bucket = 'auth' if request.url.path.startswith('/auth/') else 'general'
        limit = 10 if bucket == 'auth' else self.limit
        now = monotonic()
        key = (request.client.host if request.client else 'unknown', bucket)
        timestamps = self.requests[key]
        while timestamps and timestamps[0] <= now - self.window_seconds:
            timestamps.popleft()
        if len(timestamps) >= limit:
            retry_after = max(1, int(self.window_seconds - (now - timestamps[0])))
            return JSONResponse(
                status_code=429,
                content={'detail': 'Too many requests'},
                headers={'Retry-After': str(retry_after)},
            )
        timestamps.append(now)
        return await call_next(request)
