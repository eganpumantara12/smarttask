import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import case, select
from sqlalchemy.orm import Session, joinedload

from ..config import settings
from ..database import get_db, utcnow
from ..deps import get_current_user
from ..logging_conf import log_event
from ..models import Course, Task, User
from ..schemas import StatusIn, TaskIn, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
log = logging.getLogger("smarttask.tasks")


def _to_out(t: Task) -> TaskOut:
    now = utcnow()
    unfinished = t.status != "done"
    return TaskOut(
        id=t.id,
        title=t.title,
        description=t.description,
        deadline=t.deadline,
        status=t.status,
        course_id=t.course_id,
        course_name=t.course.name,
        course_color=t.course.color,
        is_overdue=unfinished and t.deadline < now,
        is_due_soon=unfinished and now <= t.deadline <= now + timedelta(hours=settings.due_soon_hours),
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _owned_task(db: Session, user: User, task_id: int) -> Task:
    task = db.scalar(
        select(Task).options(joinedload(Task.course)).where(Task.id == task_id, Task.user_id == user.id)
    )
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Tugas tidak ditemukan.")
    return task


def _owned_course_id(db: Session, user: User, course_id: int) -> int:
    ok = db.scalar(select(Course.id).where(Course.id == course_id, Course.user_id == user.id))
    if ok is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Mata kuliah tidak valid.")
    return ok


@router.get("", response_model=list[TaskOut])
def list_tasks(
    course_id: int | None = None,
    status_filter: str | None = Query(default=None, alias="status", pattern="^(todo|doing|done)$"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Tugas milik pengguna, diurutkan menurut prioritas: yang belum selesai dulu, deadline terdekat di atas."""
    q = select(Task).options(joinedload(Task.course)).where(Task.user_id == user.id)
    if course_id is not None:
        q = q.where(Task.course_id == course_id)
    if status_filter:
        q = q.where(Task.status == status_filter)
    q = (
        q.order_by(case((Task.status == "done", 1), else_=0), Task.deadline.asc(), Task.id.asc())
        .limit(limit)
        .offset(offset)
    )
    return [_to_out(t) for t in db.scalars(q).all()]


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: TaskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_course_id(db, user, data.course_id)
    task = Task(
        user_id=user.id,
        course_id=data.course_id,
        title=data.title,
        description=data.description,
        deadline=data.deadline,
        status="todo",
    )
    db.add(task)
    db.commit()
    log_event(log, "task_create", user_id=user.id, task_id=task.id, result="ok")
    return _to_out(_owned_task(db, user, task.id))


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _to_out(_owned_task(db, user, task_id))


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int, data: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    task = _owned_task(db, user, task_id)
    changes = data.model_dump(exclude_unset=True)
    if "course_id" in changes and changes["course_id"] is not None:
        _owned_course_id(db, user, changes["course_id"])
    for field in ("title", "course_id", "deadline", "status"):
        if field in changes and changes[field] is not None:
            setattr(task, field, changes[field])
    if "description" in changes and changes["description"] is not None:
        task.description = changes["description"]
    db.commit()
    log_event(log, "task_update", user_id=user.id, task_id=task.id, result="ok")
    return _to_out(_owned_task(db, user, task.id))


@router.patch("/{task_id}/status", response_model=TaskOut)
def set_status(
    task_id: int, data: StatusIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    task = _owned_task(db, user, task_id)
    task.status = data.status
    db.commit()
    log_event(log, "task_status", user_id=user.id, task_id=task.id, status=data.status, result="ok")
    return _to_out(_owned_task(db, user, task.id))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    task = _owned_task(db, user, task_id)
    db.delete(task)
    db.commit()
    log_event(log, "task_delete", user_id=user.id, task_id=task_id, result="ok")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
