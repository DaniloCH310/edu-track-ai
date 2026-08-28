import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields
        super().__init__(message)

VALIDATION_MESSAGES = {
    "int_parsing": "A entrada deve ser um número inteiro válido.",
    "missing": "Este campo é obrigatório.",
    "string_too_short": "O texto informado é menor que o permitido.",
    "string_too_long": "O texto informado é maior que o permitido.",
}


def error_payload(
    code: str, message: str, fields: dict[str, str] | None = None
) -> dict[str, dict[str, str | dict[str, str]]]:
    return {"error": {"code": code, "message": message, "fields": fields or {}}}


def register_error_handlers(application: FastAPI) -> None:
    @application.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exception: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exception.status_code,
            content=error_payload(
                exception.code, exception.message, exception.fields
            ),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exception: RequestValidationError
    ) -> JSONResponse:
        fields = {
            ".".join(str(part) for part in error["loc"]): VALIDATION_MESSAGES.get(
                error["type"], "Valor inválido."
            )
            for error in exception.errors()
        }
        return JSONResponse(
            status_code=422,
            content=error_payload(
                "validation_error", "Revise os campos informados.", fields
            ),
        )

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exception: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled request error",
            extra={"method": request.method, "path": request.url.path},
            exc_info=exception,
        )
        return JSONResponse(
            status_code=500,
            content=error_payload(
                "internal_error", "Não foi possível concluir a operação."
            ),
        )
