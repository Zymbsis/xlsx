from pydantic import BaseModel


class ColumnMapping(BaseModel):
    company_name_column: int | None
    domain_column: int | None
    has_header: bool
