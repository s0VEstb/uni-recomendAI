from sqlalchemy import Integer, ForeignKey, Enum, Index, String, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.enums import Currency
from typing import Optional, List
from app.db.base import Base, TimestampMixin
from app.db.enums import TagType


class Tag(TimestampMixin, Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    type: Mapped[TagType] = mapped_column(Enum(TagType), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    program_links: Mapped[List["ProgramTag"]] = relationship(back_populates="tag")
    submission_links: Mapped[List["SubmissionTag"]] = relationship(back_populates="tag")


class ProgramTag(Base):
    __tablename__ = "program_tags"

    program_id: Mapped[int] = mapped_column(
        ForeignKey("programs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="RESTRICT"),
        primary_key=True,
    )

    # optional: how strongly tag describes program
    weight: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    program: Mapped["Program"] = relationship(back_populates="tag_links")
    tag: Mapped["Tag"] = relationship(back_populates="program_links")

    __table_args__ = (
        Index("ix_program_tags_tag", "tag_id"),
    )
