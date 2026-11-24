import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..logging_conf import log_event
from ..models import User
from ..schemas import SettingsIn, SettingsOut

router = APIRouter(prefix="/api/me", tags=["me"])
log = logging.getLogger("smarttask.me")


@router.get("/settings", response_model=SettingsOut)
def get_settings(user: User = Depends(get_current_user)):
    return user


@router.put("/settings", response_model=SettingsOut)
def put_settings(data: SettingsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    for k, v in data.model_dump().items():
        setattr(user, k, v)
    db.commit()
    log_event(log, "settings_update", user_id=user.id, result="ok")
    return user
