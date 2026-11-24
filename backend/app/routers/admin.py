import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..database import get_db, utcnow
from ..deps import require_admin
from ..logging_conf import log_event
from ..models import Course, Task, User
from ..schemas import AdminStats, AdminUserOut, AdminUserPatch, ResetPasswordIn, UserOut
from ..security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])
log = logging.getLogger("smarttask.admin")


def _target(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pengguna tidak ditemukan.")
    return user


@router.get("/stats", response_model=AdminStats)
def stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    now = utcnow()
    count = lambda q: db.scalar(q) or 0  # noqa: E731
    return AdminStats(
        total_users=count(select(func.count(User.id))),
        active_users=count(select(func.count(User.id)).where(User.is_active.is_(True))),
        inactive_users=count(select(func.count(User.id)).where(User.is_active.is_(False))),
        new_last_7_days=count(select(func.count(User.id)).where(User.created_at >= now - timedelta(days=7))),
        active_last_24h=count(select(func.count(User.id)).where(User.last_login_at >= now - timedelta(hours=24))),
        total_courses=count(select(func.count(Course.id))),
        total_tasks=count(select(func.count(Task.id))),
        done_tasks=count(select(func.count(Task.id)).where(Task.status == "done")),
    )


@router.get("/users", response_model=list[AdminUserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.scalars(select(User).order_by(User.created_at.desc(), User.id.desc())).all()
    courses = dict(db.execute(select(Course.user_id, func.count(Course.id)).group_by(Course.user_id)).all())
    tasks = dict(db.execute(select(Task.user_id, func.count(Task.id)).group_by(Task.user_id)).all())
    open_ = dict(
        db.execute(select(Task.user_id, func.count(Task.id)).where(Task.status != "done").group_by(Task.user_id)).all()
    )
    return [
        AdminUserOut(
            id=u.id, name=u.name, email=u.email, role=u.role, is_active=u.is_active,
            created_at=u.created_at, last_login_at=u.last_login_at,
            course_count=courses.get(u.id, 0), task_count=tasks.get(u.id, 0), open_task_count=open_.get(u.id, 0),
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=UserOut)
def set_active(
    user_id: int, data: AdminUserPatch, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = _target(db, user_id)
    if user.id == admin.id and not data.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Anda tidak dapat menonaktifkan akun sendiri.")
    user.is_active = data.is_active
    db.commit()
    log_event(log, "admin_set_active", admin_id=admin.id, target_id=user.id, is_active=data.is_active, result="ok")
    return user


@router.post("/users/{user_id}/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    user_id: int, data: ResetPasswordIn, db: Session = Depends(get_db), admin: User = Depends(require_admin)
):
    user = _target(db, user_id)
    user.password_hash = hash_password(data.new_password)
    db.commit()
    log_event(log, "admin_reset_password", admin_id=admin.id, target_id=user.id, result="ok")


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = _target(db, user_id)
    if user.role == "admin":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Akun admin tidak dapat dihapus.")
    # Hapus data milik pengguna secara eksplisit (tidak bergantung pada FK cascade di SQLite).
    db.execute(delete(Task).where(Task.user_id == user.id))
    db.execute(delete(Course).where(Course.user_id == user.id))
    db.delete(user)
    db.commit()
    log_event(log, "admin_delete_user", admin_id=admin.id, target_id=user_id, result="ok")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
