import json

import pandas as pd
from groq import AsyncGroq

from app.config import settings
from app.exceptions.http import AppHTTPError
from app.exceptions.messages import LLM_EMPTY_RESPONSE
from app.llm.prompts import MAP_COLUMNS_SYSTEM_PROMPT, MAP_COLUMNS_USER_TEMPLATE
from app.schemas.column_mapping import ColumnMapping

client = AsyncGroq(api_key=settings.groq_api_key)


async def map_columns(df: pd.DataFrame) -> ColumnMapping:
    preview_df = df.head(10).copy()
    preview_df.columns = [f"col_{i}" for i in range(len(preview_df.columns))]
    preview = preview_df.to_string(index=False)

    user_message = MAP_COLUMNS_USER_TEMPLATE.format(
        n_rows=len(preview_df),
        n_cols=df.shape[1],
        preview=preview,
    )

    response = await client.chat.completions.create(
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
        raise AppHTTPError.internal_server_error(LLM_EMPTY_RESPONSE)

    data = json.loads(content)

    return ColumnMapping(**data)
