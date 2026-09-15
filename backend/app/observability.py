from __future__ import annotations

import json
import logging
import time
import uuid
import sqlite3
from pathlib import Path

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("phagex.api")


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, audit_db: str | None = None):
        super().__init__(app)
        self.audit_db = Path(audit_db) if audit_db else None
        if self.audit_db:
            self.audit_db.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.audit_db) as connection:
                connection.execute("CREATE TABLE IF NOT EXISTS request_audit (request_id TEXT PRIMARY KEY, created_at TEXT DEFAULT CURRENT_TIMESTAMP, method TEXT, path TEXT, status INTEGER, duration_ms REAL)")

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))[:128]
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            json.dumps(
                {
                    "event": "request_complete",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        )
        if self.audit_db:
            with sqlite3.connect(self.audit_db) as connection:
                connection.execute("INSERT INTO request_audit(request_id, method, path, status, duration_ms) VALUES (?, ?, ?, ?, ?)", (request_id, request.method, request.url.path, response.status_code, duration_ms))
        return response
