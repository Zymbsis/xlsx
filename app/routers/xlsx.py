from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile

from app.schemas.upload_response import UploadResponse
from app.security.security import verify_api_key
from app.services.company_domain_service import CompanyDomainServiceDep
from app.utils.file_validators import validate_nac_file, validate_sup_file

router = APIRouter(tags=["xlsx"])


@router.post("/upload", dependencies=[Depends(verify_api_key)], response_model=UploadResponse)
async def xlsx_upload(
    company_domain_service: CompanyDomainServiceDep,
    sup_file: Annotated[UploadFile, Depends(validate_sup_file)],
    nac_file: Annotated[UploadFile, Depends(validate_nac_file)],
    ws_session_id: UUID | None = None,
) -> UploadResponse:
    operation_id = await company_domain_service.process(sup_file, nac_file, ws_session_id)

    return UploadResponse(message="Success", operation_id=operation_id)
