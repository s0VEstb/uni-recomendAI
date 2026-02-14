from sqladmin import Admin, ModelView
from app.db.database import sync_engine
from app.db.models import (
    Tag, ProgramTag, Program
)
from sqladmin.filters import StaticValuesFilter, BooleanFilter
from app.db.enums import TagType
from sqladmin.filters import ForeignKeyFilter


class TagAdmin(ModelView, model=Tag):
    column_list = [Tag.id, Tag.slug, Tag.title, Tag.type, Tag.is_active]
    column_searchable_list = [Tag.slug, Tag.title]

    column_filters = [
        StaticValuesFilter(
            Tag.type,
            values=[
                (tag_type.value, tag_type.name) for tag_type in TagType
            ]
        ),
        BooleanFilter(Tag.is_active, "Active"),
    ]


class ProgramTagAdmin(ModelView, model=ProgramTag):
    identity = "program-tag"
    name = "Program Tag"
    name_plural = "Program Tags"

    column_list = [ProgramTag.program, ProgramTag.tag, ProgramTag.weight]
    form_columns = ["program", "tag", "weight"]

    column_filters = [
        ForeignKeyFilter(ProgramTag.program_id, "name", Program, "Program"),
        ForeignKeyFilter(ProgramTag.tag_id, "title", Tag, "Tag"),
    ]