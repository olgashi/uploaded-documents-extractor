import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db.models.activity_log import ActivityLog
from app.db.session import AsyncSessionLocal


class ActivityLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        response = await call_next(request)

        duration_ms = int((time.perf_counter() - start) * 1000)
        user_id = getattr(request.state, "current_user_id", None)

        try:
            async with AsyncSessionLocal() as db:
                db.add(ActivityLog(
                    user_id=user_id,
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    ip_address=request.client.host if request.client else "unknown",
                    request_id=request_id,
                    duration_ms=duration_ms,
                ))
                await db.commit()
        except Exception:
            pass  # never let logging failures affect the response

        return response
