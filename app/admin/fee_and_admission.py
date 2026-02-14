from sqladmin import Admin, ModelView
from app.db.database import sync_engine
from app.db.models import (
    ProgramFee, ProgramAdmission
)
from fastapi import HTTPException
from wtforms import HiddenField
import logging


class ProgramFeeAdmin(ModelView, model=ProgramFee):
    identity = "program-fee"
    column_list = [ProgramFee.id, ProgramFee.program_id, ProgramFee.year, ProgramFee.contract_fee, ProgramFee.currency]

    # ЯВНО говорим какие поля показывать на create/edit
    form_columns = [
        "program",
        "year",
        "contract_fee",
        "currency",
        "source_document",
        "source_page_start",
        "source_page_end",
    ]

    async def create_form(self, request):
        form = await super().create_form(request)
        pid = request.query_params.get("program_id")
        if pid and hasattr(form, "program_id"):
            form.program_id.data = int(pid)
        return form

    async def on_model_change(self, data, model, is_created, request):
        # страховка
        pid = data.get("program_id") or data.get("program") or request.query_params.get("program_id")
        if not pid:
            raise HTTPException(400, "program_id is required.")
        data["program_id"] = int(pid)
        data.pop("program", None)


class ProgramAdmissionAdmin(ModelView, model=ProgramAdmission):
    column_list = [ProgramAdmission.id, ProgramAdmission.program_id, ProgramAdmission.year, ProgramAdmission.ort_min_score]
    #column_filters = [ProgramAdmission.year]
