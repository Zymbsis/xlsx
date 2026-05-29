from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile

from app.db.session import SessionDep
from app.security.security import verify_api_key
from app.services.xlsx_service import xlsx_process
from app.utils.file_validators import validate_nac_file, validate_sup_file

router = APIRouter(tags=["xlsx"])


@router.post("/upload", dependencies=[Depends(verify_api_key)])
async def xlsx_upload(
    sup_file: Annotated[UploadFile, Depends(validate_sup_file)],
    nac_file: Annotated[UploadFile, Depends(validate_nac_file)],
    session: SessionDep,
    ws_session_id: UUID | None = None,
):
    operation_id = await xlsx_process(sup_file, nac_file, session, ws_session_id)

    return {"message": "Success", "operation_id": str(operation_id)}
