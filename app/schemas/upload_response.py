from uuid import UUID

from pydantic import BaseModel


class UploadResponse(BaseModel):
    message: str
    operation_id: UUID
