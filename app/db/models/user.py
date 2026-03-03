from sqlalchemy import Integer, String, ForeignKey, Enum, Boolean, Index, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.enums import StudyForm, Language
from app.db.base import Base, TimestampMixin
from sqlalchemy.types import JSON
from typing import Optional, List
from app.db.enums import UserRole
from sqlalchemy.dialects.postgresql import JSONB


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.applicant, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    submissions: Mapped[List["SurveySubmission"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    saved_programs: Mapped[List["SavedProgram"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return self.email


class SurveySubmission(TimestampMixin, Base):
    __tablename__ = "survey_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Core inputs
    ort_score: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_max: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # City enum value as string
    language: Mapped[Optional[Language]] = mapped_column(Enum(Language), nullable=True)

    # Дополнительные поля
    notes: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    needs_dorm: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    willing_to_relocate: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Everything else (legacy, strengths, etc.)
    answers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship(back_populates="submissions")

    tag_links: Mapped[List["SubmissionTag"]] = relationship(
        back_populates="submission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def tag_ids(self) -> list[int]:
        return [tl.tag_id for tl in self.tag_links]

    def __repr__(self):
        return f"Submission(id={self.id}, user_id={self.user_id})"



class SubmissionTag(Base):
    __tablename__ = "submission_tags"

    submission_id: Mapped[int] = mapped_column(
        ForeignKey("survey_submissions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    submission: Mapped["SurveySubmission"] = relationship(back_populates="tag_links")
    tag: Mapped["Tag"] = relationship(back_populates="submission_links")

    __table_args__ = (Index("ix_submission_tags_tag", "tag_id"),)

    def __repr__(self):
        return f"SubmissionTag(submission_id={self.submission_id}, tag_id={self.tag_id})"


class SavedProgram(TimestampMixin, Base):
    __tablename__ = "saved_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    user: Mapped["User"] = relationship(back_populates="saved_programs")
    program: Mapped["Program"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "program_id", name="uq_saved_user_program"),
    )

    def __repr__(self):
        return f"SavedProgram(user_id={self.user_id}, program_id={self.program_id})"