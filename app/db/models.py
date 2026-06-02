import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UploadOperation(Base):
    __tablename__ = "upload_operation"


class CompanyDomain(Base):
    __tablename__ = "company_domain"

    domain: Mapped[str]
    name: Mapped[str | None]

    operation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("upload_operation.id", ondelete="CASCADE"))
