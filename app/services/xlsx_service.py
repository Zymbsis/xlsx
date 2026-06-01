import asyncio
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, UploadFile
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyDomain, UploadOperation
from app.llm.column_mapper import map_columns
from app.schemas.column_mapping import ColumnMapping
from app.schemas.ws_events import ErrorEvent, ProcessEvent, SuccessEvent
from app.ws.manager import ws_manager


async def xlsx_process(
    sup_file: UploadFile,
    nac_file: UploadFile,
    session: AsyncSession,
    redis: Redis,
    ws_session_id: UUID | None = None,
) -> UUID:
    try:
        await ws_manager.publish(redis, ws_session_id, ProcessEvent(stage="reading_files"))

        sup_df = pd.read_excel(sup_file.file, header=None).dropna(how="all")
        nac_df = pd.read_excel(nac_file.file, header=None).dropna(how="all")

        if sup_df.empty and nac_df.empty:
            raise HTTPException(status_code=422, detail="Both files are empty")
        if nac_df.empty:
            raise HTTPException(status_code=422, detail="NAC file is empty")

        await ws_manager.publish(redis, ws_session_id, ProcessEvent(stage="mapping_columns"))

        sup_mapping, nac_mapping = await asyncio.gather(map_columns(sup_df), map_columns(nac_df))

        if None in (sup_mapping.domain_column, nac_mapping.domain_column):
            raise HTTPException(status_code=422, detail="Domain column not found in one of the files")

        await ws_manager.publish(redis, ws_session_id, ProcessEvent(stage="normalizing"))

        sup_df = process_df(sup_df, sup_mapping, include_company_name=False)
        nac_df = process_df(nac_df, nac_mapping)
        sup_df = normalize_df_domains(sup_df)
        nac_df = normalize_df_domains(nac_df)

        await ws_manager.publish(redis, ws_session_id, ProcessEvent(stage="subtracting"))

        nac_df = nac_df[~nac_df[0].isin(sup_df[0])]

        if nac_df.empty:
            raise HTTPException(status_code=422, detail="Result is empty after subtraction")

        nac_df = normalize_df_names(nac_df)

        await ws_manager.publish(redis, ws_session_id, ProcessEvent(stage="saving"))

        operation = UploadOperation()
        session.add(operation)
        await session.flush()
        records = [
            CompanyDomain(
                operation_id=operation.id,
                domain=row[0],
                name=row[1] if len(nac_df.columns) > 1 else None,
            )
            for _, row in nac_df.iterrows()
        ]
        session.add_all(records)
        await session.commit()

        await ws_manager.publish(redis, ws_session_id, SuccessEvent(operation_id=str(operation.id)))
    except HTTPException as e:
        await ws_manager.publish(redis, ws_session_id, ErrorEvent(detail=e.detail))
        raise
    else:
        return operation.id


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
