from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile

from app.db.redis import RedisDep
from app.repositories.company_domain_repository import CompanyDomainRepoDep
from app.schemas.upload_response import UploadResponse
from app.security.security import verify_api_key
from app.services.xlsx_service import xlsx_process
from app.utils.file_validators import validate_nac_file, validate_sup_file
from app.ws.manager import WSManagerDep

router = APIRouter(tags=["xlsx"])


@router.post("/upload", dependencies=[Depends(verify_api_key)], response_model=UploadResponse)
async def xlsx_upload(
    company_domain_repo: CompanyDomainRepoDep,
    redis: RedisDep,
    ws_manager: WSManagerDep,
    sup_file: Annotated[UploadFile, Depends(validate_sup_file)],
    nac_file: Annotated[UploadFile, Depends(validate_nac_file)],
    ws_session_id: UUID | None = None,
) -> UploadResponse:
    operation_id = await xlsx_process(
        sup_file,
        nac_file,
        company_domain_repo,
        redis,
        ws_manager,
        ws_session_id,
    )

    return UploadResponse(message="Success", operation_id=operation_id)
