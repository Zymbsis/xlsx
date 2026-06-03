import asyncio
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, UploadFile
from redis.asyncio import Redis

from app.db.redis import RedisDep
from app.exceptions.http import AppHTTPError
from app.exceptions.messages import (
    BOTH_FILES_EMPTY,
    DOMAIN_COLUMN_NOT_FOUND,
    NAC_FILE_EMPTY,
    RESULT_EMPTY_AFTER_SUBTRACTION,
)
from app.llm.column_mapper import map_columns
from app.repositories.company_domain_repository import CompanyDomainRepoDep, CompanyDomainRepository
from app.schemas.ws_events import ErrorEvent, ProcessEvent, SuccessEvent, WSEvent
from app.services.company_domain_data_service import CompanyDomainDataServiceDep
from app.ws.manager import WebSocketManager, WSManagerDep


class CompanyDomainService:
    def __init__(
        self,
        company_domain_data_service: CompanyDomainDataServiceDep,
        company_domain_repo: CompanyDomainRepository,
        ws_manager: WebSocketManager,
        redis: Redis,
    ) -> None:
        self._company_domain_data_service = company_domain_data_service
        self._company_domain_repo = company_domain_repo
        self._ws = ws_manager
        self._redis = redis

    async def process(self, sup_file: UploadFile, nac_file: UploadFile, ws_session_id: UUID | None = None) -> UUID:
        try:
            await self._notify(ws_session_id, ProcessEvent(stage="reading_files"))

            sup_df, nac_df = (
                self._company_domain_data_service.get_df(sup_file.file),
                self._company_domain_data_service.get_df(nac_file.file),
            )

            if sup_df.empty and nac_df.empty:
                raise AppHTTPError.unprocessable(BOTH_FILES_EMPTY)
            if nac_df.empty:
                raise AppHTTPError.unprocessable(NAC_FILE_EMPTY)

            await self._notify(ws_session_id, ProcessEvent(stage="mapping_columns"))

            sup_mapping, nac_mapping = await asyncio.gather(map_columns(sup_df), map_columns(nac_df))

            if None in (sup_mapping.domain_column, nac_mapping.domain_column):
                raise AppHTTPError.unprocessable(DOMAIN_COLUMN_NOT_FOUND)

            await self._notify(ws_session_id, ProcessEvent(stage="normalizing"))

            sup_df, nac_df = (
                self._company_domain_data_service.process_df(sup_df, sup_mapping, include_company_name=False),
                self._company_domain_data_service.process_df(nac_df, nac_mapping),
            )

            sup_df, nac_df = (
                self._company_domain_data_service.normalize_df_domains(sup_df),
                self._company_domain_data_service.normalize_df_domains(nac_df),
            )

            await self._notify(ws_session_id, ProcessEvent(stage="subtracting"))

            nac_df = self._company_domain_data_service.subtract_sup_domains(nac_df, sup_df)

            if nac_df.empty:
                raise AppHTTPError.unprocessable(RESULT_EMPTY_AFTER_SUBTRACTION)

            nac_df = self._company_domain_data_service.normalize_df_names(nac_df)

            await self._notify(ws_session_id, ProcessEvent(stage="saving"))

            company_domain_records = self._company_domain_data_service.build_company_domain_records(nac_df)
            operation_id = await self._company_domain_repo.save_many(company_domain_records)

            await self._notify(ws_session_id, SuccessEvent(operation_id=str(operation_id)))
        except HTTPException as e:
            await self._notify(ws_session_id, ErrorEvent(detail=e.detail))
            raise
        else:
            return operation_id

    async def _notify(
        self,
        ws_session_id: UUID | None,
        event: WSEvent,
    ) -> None:
        await self._ws.publish(self._redis, ws_session_id, event)


def get_company_domain_service(
    company_domain_data_service: CompanyDomainDataServiceDep,
    company_domain_repo: CompanyDomainRepoDep,
    ws_manager: WSManagerDep,
    redis: RedisDep,
) -> CompanyDomainService:
    return CompanyDomainService(company_domain_data_service, company_domain_repo, ws_manager, redis)


CompanyDomainServiceDep = Annotated[CompanyDomainService, Depends(get_company_domain_service)]
