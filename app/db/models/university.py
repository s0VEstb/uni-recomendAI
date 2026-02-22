from sqlalchemy import Integer, String, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.enums import StudyForm, Language
from app.db.base import Base, TimestampMixin
from sqlalchemy.types import JSON
from typing import Optional, List


class University(TimestampMixin, Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    website: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    photo_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    contacts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    programs: Mapped[List["Program"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    documents: Mapped[List["Document"]] = relationship(
        back_populates="university",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"{self.name}"



class Program(TimestampMixin, Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    university_id: Mapped[int] = mapped_column(
        ForeignKey("universities.id"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language: Mapped[Language] = mapped_column(Enum(Language), nullable=False, index=True)
    study_form: Mapped[StudyForm] = mapped_column(Enum(StudyForm), nullable=False, index=True)
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False)
    official_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    university: Mapped["University"] = relationship(back_populates="programs")

    admissions: Mapped[List["ProgramAdmission"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    fees: Mapped[List["ProgramFee"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    tag_links: Mapped[List["ProgramTag"]] = relationship(
        back_populates="program",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_programs_university_lang_form_active", "university_id", "language", "study_form", "is_active"),
    )

    def __repr__(self) -> str:
        return f"id={self.id} - {self.name}"
