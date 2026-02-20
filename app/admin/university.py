from sqladmin import Admin, ModelView
from app.db.database import sync_engine
from app.db.models import (
    University, Program
)
from markupsafe import Markup
from sqladmin.filters import ForeignKeyFilter


class UniversityAdmin(ModelView, model=University):
    column_list = [University.id, University.name, University.city, University.website]
    column_searchable_list = [University.name, University.city]
    column_sortable_list = [University.id, University.name, University.city]


class ProgramAdmin(ModelView, model=Program):
    column_list = [Program.id, Program.university ,Program.name, Program.university_id]
    column_searchable_list = [Program.name]

    column_formatters = {
        Program.id: lambda m, a: Markup(
            f'{m.id}&nbsp;'
            f'<a class="btn btn-sm btn-primary" href="/admin/program-fee/create?program_id={m.id}">+ Fee</a>'
        )
    }
    
    column_filters = [
        ForeignKeyFilter(Program.university_id, "name", University, "Program"),
    ]