from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Что-то пошло не так. Мы уже чиним. Попробуйте обновить страницу."

    def __init__(self, message: str | None = None, status_code: int | None = None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404


class AuthError(AppError):
    status_code = 401
    message = "Нужно войти в аккаунт, чтобы продолжить."


class ForbiddenError(AppError):
    status_code = 403
    message = "Нет доступа к этому разделу."


class ConflictError(AppError):
    status_code = 409


class RateLimitError(AppError):
    status_code = 429
    message = "Слишком много запросов. Подождите немного и попробуйте снова."


class ProviderError(AppError):
    status_code = 502


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        import structlog

        structlog.get_logger().error("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Что-то пошло не так. Мы уже чиним. Попробуйте обновить страницу."},
        )
