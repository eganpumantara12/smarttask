from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.email_service import send_task_reminder_email

scheduler = BackgroundScheduler()


def check_and_send_email_reminders() -> None:
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        pending_tasks = (
            db.query(Task)
            .filter(Task.is_completed.is_(False), Task.email_reminded.is_(False))
            .all()
        )

        for task in pending_tasks:
            if not getattr(task, "deadline", None):
                continue

            deadline = task.deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)

            user = db.query(User).filter(User.id == task.user_id).first()
            if not user or not getattr(user, "is_verified", False):
                continue

            lead_hours = getattr(user, "reminder_hours_before", None) or 3
            time_left = deadline - now

            if timedelta(minutes=0) < time_left <= timedelta(hours=lead_hours):
                course_obj = getattr(task, "course", None)
                course_name = getattr(course_obj, "name", "-") if course_obj else "-"
                deadline_wita = deadline.astimezone(timezone(timedelta(hours=8))).strftime(
                    "%d %b %Y, %H:%M WITA"
                )
                hours_left = max(1, int(time_left.total_seconds() // 3600))

                sent = send_task_reminder_email(
                    to_email=user.email,
                    task_title=task.title,
                    course_name=course_name,
                    deadline_str=deadline_wita,
                    hours_left=hours_left,
                )
                if sent:
                    task.email_reminded = True
                    db.commit()
    finally:
        db.close()


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            check_and_send_email_reminders,
            trigger="interval",
            minutes=1,
            id="smarttask_email_reminder",
            replace_existing=True,
        )
        scheduler.start()