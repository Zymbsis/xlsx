from pydantic import BaseModel


class CompanyDomainCreate(BaseModel):
    domain: str
    name: str | None = None
