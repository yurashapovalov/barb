"""Structured error responses — unified format for all endpoints."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from api.request_id import get_request_id

log = logging.getLogger(__name__)

STATUS_TO_CODE = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "UNAUTHORIZED",
    404: "NOT_FOUND",
    422: "VALIDATION_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _error_response(status: int, message: str) -> JSONResponse:
    code = STATUS_TO_CODE.get(status, "INTERNAL_ERROR")
    return JSONResponse(
        status_code=status,
        content={"error": message, "code": code, "request_id": get_request_id()},
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_request: Request, exc: HTTPException):
        return _error_response(exc.status_code, exc.detail)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        return _error_response(422, "Validation error")

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, exc: Exception):
        log.exception("Unhandled exception")
        return _error_response(500, "Internal server error")
