from sqladmin import Admin, ModelView
from app.db.database import sync_engine
from app.db.models import (
    User, SurveySubmission, SavedProgram
)


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.role, User.is_active]
    column_searchable_list = [User.email]
    #column_filters = [User.role, User.is_active]


class SurveySubmissionAdmin(ModelView, model=SurveySubmission):
    column_list = [
        SurveySubmission.id,
        SurveySubmission.user_id,
        SurveySubmission.ort_score,
        SurveySubmission.city,
        SurveySubmission.language,
        "tag_links"
    ]

    column_formatters = {
        "tag_links": lambda value, column: ", ".join(value) if isinstance(value, list) else ""
    }




class SavedProgramAdmin(ModelView, model=SavedProgram):
    column_list = [SavedProgram.id, SavedProgram.user_id, SavedProgram.program_id]