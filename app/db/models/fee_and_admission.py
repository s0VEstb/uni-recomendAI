from sqlalchemy import Integer, ForeignKey, Enum, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.enums import Currency
from app.db.base import Base, TimestampMixin
from sqlalchemy.dialects.postgresql import JSONB


class ProgramFee(TimestampMixin, Base):
    __tablename__ = "program_fees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Сумма в минимальных единицах? (обычно просто int в валюте)
    contract_fee: Mapped[int] = mapped_column(Integer, nullable=False)

    currency: Mapped[Currency] = mapped_column(Enum(Currency), nullable=False)

    # Source (обязательно)
    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    program: Mapped["Program"] = relationship(back_populates="fees")
    source_document: Mapped["Document"] = relationship()

    __table_args__ = (
        # на одну программу один fee на год (без дублей)
        UniqueConstraint("program_id", "year", name="uq_program_fee_program_year"),
        Index("ix_program_fee_program_year", "program_id", "year"),
        Index("ix_program_fee_year_currency", "year", "currency"),
    )


class ProgramAdmission(TimestampMixin, Base):
    __tablename__ = "program_admissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Если для части программ ОРТ не нужен — nullable
    ort_min_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Всё, что сложно нормализовать в MVP
    requirements: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    deadlines: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    source_document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    program: Mapped["Program"] = relationship(back_populates="admissions")
    source_document: Mapped["Document"] = relationship()

    __table_args__ = (
        UniqueConstraint("program_id", "year", name="uq_program_adm_program_year"),
        Index("ix_program_adm_program_year", "program_id", "year"),
        Index("ix_program_adm_year_ort", "year", "ort_min_score"),
    )
