import asyncio
from typing import Annotated
from uuid import UUID

import pandas as pd
from fastapi import Depends, HTTPException, UploadFile
from redis.asyncio import Redis

from app.db.redis import RedisDep
from app.llm.column_mapper import map_columns
from app.repositories.company_domain_repository import CompanyDomainRepoDep, CompanyDomainRepository
from app.schemas.column_mapping import ColumnMapping
from app.schemas.company_domain import CompanyDomainCreate
from app.schemas.ws_events import ErrorEvent, ProcessEvent, SuccessEvent, WSEvent
from app.ws.manager import WebSocketManager, WSManagerDep


class CompanyDomainService:
    def __init__(
        self, company_domain_repo: CompanyDomainRepository, ws_manager: WebSocketManager, redis: Redis
    ) -> None:
        self._company_domain_repo = company_domain_repo
        self._ws = ws_manager
        self._redis = redis

    async def process(self, sup_file: UploadFile, nac_file: UploadFile, ws_session_id: UUID | None = None) -> UUID:
        try:
            await self._notify(ws_session_id, ProcessEvent(stage="reading_files"))

            sup_df = pd.read_excel(sup_file.file, header=None).dropna(how="all")
            nac_df = pd.read_excel(nac_file.file, header=None).dropna(how="all")

            if sup_df.empty and nac_df.empty:
                raise HTTPException(status_code=422, detail="Both files are empty")
            if nac_df.empty:
                raise HTTPException(status_code=422, detail="NAC file is empty")

            await self._notify(ws_session_id, ProcessEvent(stage="mapping_columns"))

            sup_mapping, nac_mapping = await asyncio.gather(map_columns(sup_df), map_columns(nac_df))

            if None in (sup_mapping.domain_column, nac_mapping.domain_column):
                raise HTTPException(status_code=422, detail="Domain column not found in one of the files")

            await self._notify(ws_session_id, ProcessEvent(stage="normalizing"))

            sup_df = process_df(sup_df, sup_mapping, include_company_name=False)
            nac_df = process_df(nac_df, nac_mapping)
            sup_df = normalize_df_domains(sup_df)
            nac_df = normalize_df_domains(nac_df)

            await self._notify(ws_session_id, ProcessEvent(stage="subtracting"))

            nac_df = nac_df[~nac_df[0].isin(sup_df[0])]

            if nac_df.empty:
                raise HTTPException(status_code=422, detail="Result is empty after subtraction")

            nac_df = normalize_df_names(nac_df)

            await self._notify(ws_session_id, ProcessEvent(stage="saving"))

            operation_id = await self._company_domain_repo.save_many(self._to_domains(nac_df))

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

    @staticmethod
    def _to_domains(nac_df: pd.DataFrame) -> list[CompanyDomainCreate]:
        return [
            CompanyDomainCreate(domain=rec[0], name=None if pd.isna(v := rec.get(1)) else v or None)
            for rec in nac_df.to_dict(orient="records")
        ]


def get_company_domain_service(
    company_domain_repo: CompanyDomainRepoDep, ws_manager: WSManagerDep, redis: RedisDep
) -> CompanyDomainService:
    return CompanyDomainService(company_domain_repo, ws_manager, redis)


CompanyDomainServiceDep = Annotated[CompanyDomainService, Depends(get_company_domain_service)]


def process_df(df: pd.DataFrame, mapping: ColumnMapping, include_company_name: bool = True) -> pd.DataFrame:
    if mapping.domain_column is None:
        raise ValueError("domain_column is required")

    if mapping.has_header:
        df = df.iloc[1:].reset_index(drop=True)

    columns = [mapping.domain_column]
    if include_company_name and mapping.company_name_column is not None:
        columns.append(mapping.company_name_column)

    df = df.iloc[:, columns]
    df.columns = pd.RangeIndex(len(df.columns))

    return df


def normalize_df_domains(df: pd.DataFrame, domain_col_index: int = 0) -> pd.DataFrame:
    df[domain_col_index] = df[domain_col_index].astype(str).str.strip().str.lower()

    return df[df[domain_col_index].str.contains(r"\.", regex=True)]


def normalize_df_names(df: pd.DataFrame, name_col_index: int = 1) -> pd.DataFrame:
    if name_col_index not in df.columns:
        return df

    df[name_col_index] = df[name_col_index].str.replace(r"[^\w\s&'\-.,()\/]", "", regex=True).str.strip()

    return df
