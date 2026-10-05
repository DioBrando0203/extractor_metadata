"""Restringe cargas antes del parser multipart y acepta páginas de origen local."""

from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

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
        limit = settings.max_upload_bytes + 1024 * 1024  # margen para encabezados multipart
        try:
            declared_length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            await JSONResponse({"detail": "Tamaño de solicitud inválido."}, status_code=400)(
                scope, receive, send
            )
            return
        if declared_length > limit:
            await JSONResponse(
                {"detail": "El MSG supera el límite local de 100 MB."}, status_code=413
            )(scope, receive, send)
            return
        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > limit:
                raise HTTPException(413, detail="El MSG supera el límite local de 100 MB.")
            return message

        await self.app(scope, limited_receive, send)
