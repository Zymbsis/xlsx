import asyncio
import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile

from app.core.log_messages import PROCESS_STAGE, PROCESSING_UPLOAD, UPLOAD_COMPLETED, UPLOAD_FAILED
from app.exceptions.http import AppHTTPError
from app.exceptions.messages import (
    BOTH_FILES_EMPTY,
    DOMAIN_COLUMN_NOT_FOUND,
    NAC_FILE_EMPTY,
    RESULT_EMPTY_AFTER_SUBTRACTION,
)
from app.repositories.company_domain_repository import CompanyDomainRepoDep, CompanyDomainRepository
from app.schemas.ws_events import ErrorEvent, ProcessEvent, ProcessStage, SuccessEvent
from app.services.column_mapper_service import ColumnMapperService, ColumnMapperServiceDep
from app.services.company_domain_data_service import CompanyDomainDataServiceDep
from app.ws.manager import WebSocketManager, WSManagerDep

logger = logging.getLogger(__name__)


class CompanyDomainService:
    def __init__(
        self,
        company_domain_data_service: CompanyDomainDataServiceDep,
        column_mapper_service: ColumnMapperService,
        company_domain_repo: CompanyDomainRepository,
        ws_manager: WebSocketManager,
    ) -> None:
        self._company_domain_data_service = company_domain_data_service
        self._column_mapper_service = column_mapper_service
        self._company_domain_repo = company_domain_repo
        self._ws = ws_manager

    async def process(self, sup_file: UploadFile, nac_file: UploadFile, ws_session_id: UUID | None = None) -> UUID:
        logger.info(PROCESSING_UPLOAD, ws_session_id)

        try:
            await self._ws.publish(ws_session_id, ProcessEvent(stage=ProcessStage.READING_FILES))
            logger.info(PROCESS_STAGE, ProcessStage.READING_FILES)

            sup_df, nac_df = (
                self._company_domain_data_service.get_df(sup_file.file),
                self._company_domain_data_service.get_df(nac_file.file),
            )

            if sup_df.empty and nac_df.empty:
                raise AppHTTPError.unprocessable(BOTH_FILES_EMPTY)
            if nac_df.empty:
                raise AppHTTPError.unprocessable(NAC_FILE_EMPTY)

            await self._ws.publish(ws_session_id, ProcessEvent(stage=ProcessStage.MAPPING_COLUMNS))
            logger.info(PROCESS_STAGE, ProcessStage.MAPPING_COLUMNS)

            sup_mapping, nac_mapping = await asyncio.gather(
                self._column_mapper_service.map_columns(sup_df), self._column_mapper_service.map_columns(nac_df)
            )

            if None in (sup_mapping.domain_column, nac_mapping.domain_column):
                raise AppHTTPError.unprocessable(DOMAIN_COLUMN_NOT_FOUND)

            await self._ws.publish(ws_session_id, ProcessEvent(stage=ProcessStage.NORMALIZING))
            logger.info(PROCESS_STAGE, ProcessStage.NORMALIZING)

            sup_df, nac_df = (
                self._company_domain_data_service.process_df(sup_df, sup_mapping, include_company_name=False),
                self._company_domain_data_service.process_df(nac_df, nac_mapping),
            )

            sup_df, nac_df = (
                self._company_domain_data_service.normalize_df_domains(sup_df),
                self._company_domain_data_service.normalize_df_domains(nac_df),
            )

            await self._ws.publish(ws_session_id, ProcessEvent(stage=ProcessStage.SUBTRACTING))
            logger.info(PROCESS_STAGE, ProcessStage.SUBTRACTING)

            nac_df = self._company_domain_data_service.subtract_sup_domains(nac_df, sup_df)

            if nac_df.empty:
                raise AppHTTPError.unprocessable(RESULT_EMPTY_AFTER_SUBTRACTION)

            nac_df = self._company_domain_data_service.normalize_df_names(nac_df)

            await self._ws.publish(ws_session_id, ProcessEvent(stage=ProcessStage.SAVING))
            logger.info(PROCESS_STAGE, ProcessStage.SAVING)

            company_domain_records = self._company_domain_data_service.build_company_domain_records(nac_df)
            operation_id = await self._company_domain_repo.save_many(company_domain_records)

            await self._ws.publish(ws_session_id, SuccessEvent(operation_id=str(operation_id)))
            logger.info(UPLOAD_COMPLETED, operation_id)
        except HTTPException as e:
            logger.warning(UPLOAD_FAILED, ws_session_id, e.detail)
            await self._ws.publish(ws_session_id, ErrorEvent(detail=e.detail))
            raise
        else:
            return operation_id


def get_company_domain_service(
    company_domain_data_service: CompanyDomainDataServiceDep,
    column_mapper_service: ColumnMapperServiceDep,
    company_domain_repo: CompanyDomainRepoDep,
    ws_manager: WSManagerDep,
) -> CompanyDomainService:
    return CompanyDomainService(company_domain_data_service, column_mapper_service, company_domain_repo, ws_manager)


CompanyDomainServiceDep = Annotated[CompanyDomainService, Depends(get_company_domain_service)]
