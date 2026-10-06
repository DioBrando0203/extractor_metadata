"""Restringe el origen de llamadas a la aplicación local."""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import settings


class LocalUploadMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        headers = dict(scope["headers"])
        origin = headers.get(b"origin", b"").decode("latin-1")
        if origin and origin not in settings.allowed_origins:
            await JSONResponse(
                {"detail": "Origen no autorizado para el servicio local."}, status_code=403
            )(scope, receive, send)
            return
        await self.app(scope, receive, send)
