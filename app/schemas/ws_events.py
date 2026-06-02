from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class ProcessStage(StrEnum):
    READING_FILES = "reading_files"
    MAPPING_COLUMNS = "mapping_columns"
    NORMALIZING = "normalizing"
    SUBTRACTING = "subtracting"
    SAVING = "saving"


class ProcessEvent(BaseModel):
    type: Literal["process"] = "process"
    stage: str


class SuccessEvent(BaseModel):
    type: Literal["success"] = "success"
    operation_id: str


class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    detail: str


WSEvent = Annotated[ProcessEvent | SuccessEvent | ErrorEvent, Field(discriminator="type")]
