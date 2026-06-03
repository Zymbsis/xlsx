import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CompanyDomain, UploadOperation
from app.db.session import SessionDep
from app.schemas.company_domain import CompanyDomainCreate

logger = logging.getLogger(__name__)


class CompanyDomainRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_many(self, domains: list[CompanyDomainCreate]) -> UUID:
        logger.info("Saving %s company domain records", len(domains))

        operation = UploadOperation()
        self._session.add(operation)
        await self._session.flush()

        records = [CompanyDomain(operation_id=operation.id, domain=item.domain, name=item.name) for item in domains]
        self._session.add_all(records)
        await self._session.commit()

        logger.info("Saved company domain records operation_id=%s", operation.id)

        return operation.id


def get_company_domain_repository(session: SessionDep) -> CompanyDomainRepository:
    return CompanyDomainRepository(session)


CompanyDomainRepoDep = Annotated[CompanyDomainRepository, Depends(get_company_domain_repository)]
