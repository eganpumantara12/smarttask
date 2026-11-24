import { STATUS, formatDeadline, relativeDeadline } from '../utils'

export default function TaskCard({ task, onStatus, onEdit, onDelete }) {
  const cls = ['task', task.status === 'done' ? 'done' : '', task.is_overdue ? 'overdue' : '', task.is_due_soon ? 'soon' : '']
    .filter(Boolean).join(' ')
  return (
    <li className={cls} style={{ '--course': task.course_color }}>
      <div className="task-main">
        <div className="task-top">
          <span className="pill" style={{ '--c': task.course_color }}>{task.course_name}</span>
          {task.is_overdue && <span className="badge late">Terlambat</span>}
          {task.is_due_soon && <span className="badge soon">Segera</span>}
        </div>
        <h3 className="task-title">{task.title}</h3>
        {task.description && <p className="task-desc">{task.description}</p>}
        <p className="task-due">
          <span>{formatDeadline(task.deadline)}</span>
          {task.status !== 'done' && <span className="rel"> · {relativeDeadline(task.deadline)}</span>}
        </p>
      </div>
      <div className="task-side">
        <div className="seg" role="group" aria-label={`Status tugas ${task.title}`}>
          {STATUS.map((s) => (
            <button
              key={s.value}
              className={task.status === s.value ? `on ${s.value}` : ''}
              aria-pressed={task.status === s.value}
              onClick={() => task.status !== s.value && onStatus(task, s.value)}
              title={s.label}
            >
              {s.short}
            </button>
          ))}
        </div>
        <div className="task-actions">
          <button className="btn ghost sm" onClick={() => onEdit(task)}>Ubah</button>
          <button className="btn ghost sm danger-text" onClick={() => onDelete(task)}>Hapus</button>
        </div>
      </div>
    </li>
  )
}
