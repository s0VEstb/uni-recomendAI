from sqladmin import Admin
from app.db.database import sync_engine
from app.admin.university import UniversityAdmin, ProgramAdmin
from app.admin.document import DocumentAdmin, DocumentChunkAdmin
from app.admin.fee_and_admission import ProgramFeeAdmin, ProgramAdmissionAdmin
from app.admin.tag import TagAdmin, ProgramTagAdmin
from app.admin.user import UserAdmin, SurveySubmissionAdmin, SavedProgramAdmin


def setup_admin(app):
    admin = Admin(app, sync_engine)

    admin.add_view(UniversityAdmin)
    admin.add_view(ProgramAdmin)
    admin.add_view(DocumentAdmin)
    admin.add_view(DocumentChunkAdmin)
    admin.add_view(ProgramFeeAdmin)
    admin.add_view(ProgramAdmissionAdmin)
    admin.add_view(TagAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(SurveySubmissionAdmin)
    admin.add_view(SavedProgramAdmin)
    admin.add_view(ProgramTagAdmin)