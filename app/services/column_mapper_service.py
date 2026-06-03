import logging
from typing import Annotated

import pandas as pd
from fastapi import Depends
from groq import AsyncGroq

from app.exceptions.http import AppHTTPError
from app.llm.groq import GroqClientDep
from app.llm.prompts import MAP_COLUMNS_SYSTEM_PROMPT, MAP_COLUMNS_USER_TEMPLATE
from app.schemas.column_mapping import ColumnMapping

logger = logging.getLogger(__name__)

SAMPLE_ROW = 10


class ColumnMapperService:
    def __init__(self, groq_client: AsyncGroq) -> None:
        self._groq_client = groq_client

    async def map_columns(self, df: pd.DataFrame) -> ColumnMapping:
        logger.debug("Mapping columns for dataframe shape=%s", df.shape)

        preview_df = df.head(SAMPLE_ROW).copy()
        preview_df.columns = [f"col_{i}" for i in range(len(preview_df.columns))]
        preview = preview_df.to_string(index=False)

        user_message = MAP_COLUMNS_USER_TEMPLATE.format(
            n_rows=len(preview_df),
            n_cols=df.shape[1],
            preview=preview,
        )

        response = await self._groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": MAP_COLUMNS_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        content = response.choices[0].message.content

        if content is None:
            raise AppHTTPError.internal_server_error("LLM returned empty content")

        mapping = ColumnMapping.model_validate_json(content)

        logger.info(
            "Mapped columns domain_column=%s company_name_column=%s has_header=%s",
            mapping.domain_column,
            mapping.company_name_column,
            mapping.has_header,
        )

        return mapping


def get_column_mapper_service(groq_client: GroqClientDep) -> ColumnMapperService:
    return ColumnMapperService(groq_client)


ColumnMapperServiceDep = Annotated[ColumnMapperService, Depends(get_column_mapper_service)]
