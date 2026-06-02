from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_422_UNPROCESSABLE_CONTENT,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)


class AppHTTPError:
    @classmethod
    def create(cls, status_code: int, detail: str) -> HTTPException:
        return HTTPException(status_code, detail)

    @classmethod
    def bad_request(cls, detail: str) -> HTTPException:
        return cls.create(HTTP_400_BAD_REQUEST, detail)

    @classmethod
    def forbidden(cls, detail: str) -> HTTPException:
        return cls.create(HTTP_403_FORBIDDEN, detail)

    @classmethod
    def unprocessable(cls, detail: str) -> HTTPException:
        return cls.create(HTTP_422_UNPROCESSABLE_CONTENT, detail=detail)

    @classmethod
    def internal_server_error(cls, detail: str) -> HTTPException:
        return cls.create(HTTP_500_INTERNAL_SERVER_ERROR, detail)

    @classmethod
    def service_unavailable(cls, detail: str) -> HTTPException:
        return cls.create(HTTP_503_SERVICE_UNAVAILABLE, detail)
