import datetime

from sqlalchemy import func, String, ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase,
    declared_attr,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.types import LargeBinary


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls):
        return cls.__name__.lower()

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        onupdate=func.now(), nullable=True
    )


class Employee(Base):
    fullname: Mapped[str] = mapped_column(String(50))
    encoding_id: Mapped[int] = mapped_column(ForeignKey("encoding.id"))
    image_id: Mapped[int] = mapped_column(ForeignKey("image.id"))

    encoding: Mapped["Encoding"] = relationship(back_populates="employee")
    image: Mapped["Image"] = relationship(back_populates="employee")


class Image(Base):
    path: Mapped[str]

    employee: Mapped["Employee"] = relationship(back_populates="image")


class Encoding(Base):
    encoding = mapped_column(LargeBinary)

    employee: Mapped["Employee"] = relationship(back_populates="encoding")
