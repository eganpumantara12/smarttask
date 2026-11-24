import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..logging_conf import log_event
from ..models import Course, Task, User
from ..schemas import CourseIn, CourseOut

router = APIRouter(prefix="/api/courses", tags=["courses"])
log = logging.getLogger("smarttask.courses")


def _owned_course(db: Session, user: User, course_id: int) -> Course:
    # Selalu difilter dengan user_id: milik pengguna lain dianggap tidak ada (404).
    course = db.scalar(select(Course).where(Course.id == course_id, Course.user_id == user.id))
    if course is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Mata kuliah tidak ditemukan.")
    return course


def _out(course: Course, total: int, open_: int) -> CourseOut:
    return CourseOut(id=course.id, name=course.name, color=course.color, task_count=total, open_task_count=open_)


@router.get("", response_model=list[CourseOut])
def list_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        select(Course, func.count(Task.id))
        .outerjoin(Task, Task.course_id == Course.id)
        .where(Course.user_id == user.id)
        .group_by(Course.id)
        .order_by(Course.name)
    ).all()
    # Hitung tugas belum selesai terpisah agar portabel antara SQLite dan PostgreSQL.
    open_counts = dict(
        db.execute(
            select(Task.course_id, func.count(Task.id))
            .where(Task.user_id == user.id, Task.status != "done")
            .group_by(Task.course_id)
        ).all()
    )
    return [_out(c, total, open_counts.get(c.id, 0)) for c, total in rows]


@router.post("", response_model=CourseOut, status_code=status.HTTP_201_CREATED)
def create_course(data: CourseIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exists = db.scalar(
        select(Course).where(Course.user_id == user.id, func.lower(Course.name) == data.name.lower())
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Mata kuliah dengan nama itu sudah ada.")
    course = Course(user_id=user.id, name=data.name, color=data.color)
    db.add(course)
    db.commit()
    log_event(log, "course_create", user_id=user.id, course_id=course.id, result="ok")
    return _out(course, 0, 0)


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int, data: CourseIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    course = _owned_course(db, user, course_id)
    dup = db.scalar(
        select(Course).where(
            Course.user_id == user.id, func.lower(Course.name) == data.name.lower(), Course.id != course.id
        )
    )
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "Mata kuliah dengan nama itu sudah ada.")
    course.name, course.color = data.name, data.color
    db.commit()
    log_event(log, "course_update", user_id=user.id, course_id=course.id, result="ok")
    total = db.scalar(select(func.count(Task.id)).where(Task.course_id == course.id)) or 0
    open_ = db.scalar(select(func.count(Task.id)).where(Task.course_id == course.id, Task.status != "done")) or 0
    return _out(course, total, open_)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    course = _owned_course(db, user, course_id)
    db.delete(course)  # tugas di dalamnya ikut terhapus (cascade)
    db.commit()
    log_event(log, "course_delete", user_id=user.id, course_id=course_id, result="ok")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
