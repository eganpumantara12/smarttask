import { useCallback, useEffect, useMemo, useState } from 'react'
import { Courses, Tasks } from '../api'
import TaskCard from '../components/TaskCard.jsx'
import TaskForm from '../components/TaskForm.jsx'
import { ConfirmDialog, Empty } from '../components/ui.jsx'

export default function TasksPage({ user, notify }) {
  const [tasks, setTasks] = useState(null)
  const [courses, setCourses] = useState([])
  const [courseId, setCourseId] = useState('')
  const [showDone, setShowDone] = useState(true)
  const [form, setForm] = useState(null) // null | {task?}
  const [toDelete, setToDelete] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [t, c] = await Promise.all([Tasks.list(), Courses.list()])
      setTasks(t)
      setCourses(c)
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])
  useEffect(() => { load() }, [load])

  const visible = useMemo(
    () => (tasks || []).filter((t) => (!courseId || t.course_id === Number(courseId)) && (showDone || t.status !== 'done')),
    [tasks, courseId, showDone],
  )
  const stats = useMemo(() => {
    const all = tasks || []
    return {
      late: all.filter((t) => t.is_overdue).length,
      soon: all.filter((t) => t.is_due_soon).length,
      open: all.filter((t) => t.status !== 'done').length,
      done: all.filter((t) => t.status === 'done').length,
    }
  }, [tasks])

  const changeStatus = async (task, status) => {
    try {
      await Tasks.setStatus(task.id, status)
      await load() // urutan & penanda mengikuti server
      if (status === 'done') notify('Tugas ditandai selesai. 🎉')
    } catch (e) { notify(e.message, 'err') }
  }
  const remove = async () => {
    const t = toDelete
    setToDelete(null)
    try { await Tasks.remove(t.id); notify('Tugas dihapus.'); load() } catch (e) { notify(e.message, 'err') }
  }

  const hour = new Date().getHours()
  const greet = hour < 11 ? 'Selamat pagi' : hour < 15 ? 'Selamat siang' : hour < 18 ? 'Selamat sore' : 'Selamat malam'

  if (error && !tasks) return <div className="panel"><div className="error-note">{error}</div><button className="btn" onClick={load}>Coba lagi</button></div>
  if (!tasks) return <p className="muted center">Memuat tugas…</p>

  return (
    <>
      <div className="page-head">
        <div>
          <h1>{greet}, {user.name.split(' ')[0]}</h1>
          <p className="muted">
            {stats.open === 0 ? 'Semua tugas sudah beres. Nikmati harimu!' : `${stats.open} tugas belum selesai${stats.late ? `, ${stats.late} terlambat` : ''}.`}
          </p>
        </div>
        <button className="btn primary fab" onClick={() => (courses.length ? setForm({}) : notify('Tambahkan mata kuliah dulu di menu Mata Kuliah.', 'err'))}>
          <span aria-hidden="true">＋</span> Tugas baru
        </button>
      </div>

      <div className="stats">
        <Stat label="Terlambat" value={stats.late} tone="late" />
        <Stat label="Segera (≤ 48 jam)" value={stats.soon} tone="soon" />
        <Stat label="Belum selesai" value={stats.open} />
        <Stat label="Selesai" value={stats.done} tone="done" />
      </div>

      <div className="filters">
        <div className="chips" role="group" aria-label="Filter mata kuliah">
          <button className={`chip ${courseId === '' ? 'on' : ''}`} onClick={() => setCourseId('')}>Semua</button>
          {courses.map((c) => (
            <button key={c.id} className={`chip ${String(c.id) === String(courseId) ? 'on' : ''}`} style={{ '--c': c.color }} onClick={() => setCourseId(String(c.id))}>
              <i className="dot" /> {c.name}{c.open_task_count ? <small>{c.open_task_count}</small> : null}
            </button>
          ))}
        </div>
        <label className="check"><input type="checkbox" checked={showDone} onChange={(e) => setShowDone(e.target.checked)} /> Tampilkan yang selesai</label>
      </div>

      {courses.length === 0 ? (
        <Empty title="Mulai dengan menambah mata kuliah">
          Buka menu <a href="#/matkul">Mata Kuliah</a>, tambahkan mata kuliah semester ini, lalu catat tugas pertamamu.
        </Empty>
      ) : visible.length === 0 ? (
        <Empty title={tasks.length ? 'Tidak ada tugas yang cocok' : 'Belum ada tugas'}>
          {tasks.length ? 'Coba ubah filter mata kuliah.' : 'Klik “Tugas baru” untuk mencatat tugas pertamamu.'}
        </Empty>
      ) : (
        <ul className="tasklist">
          {visible.map((t) => (
            <TaskCard key={t.id} task={t} onStatus={changeStatus} onEdit={(task) => setForm({ task })} onDelete={setToDelete} />
          ))}
        </ul>
      )}

      {form && (
        <TaskForm
          task={form.task}
          courses={courses}
          defaultCourseId={courseId ? Number(courseId) : undefined}
          onClose={() => setForm(null)}
          onSaved={(_, created) => { setForm(null); notify(created ? 'Tugas tersimpan.' : 'Perubahan tersimpan.'); load() }}
        />
      )}
      {toDelete && (
        <ConfirmDialog title="Hapus tugas?" message={`“${toDelete.title}” akan dihapus permanen.`} onConfirm={remove} onClose={() => setToDelete(null)} />
      )}
    </>
  )
}

function Stat({ label, value, tone }) {
  return (
    <div className={`stat ${tone || ''} ${value > 0 ? 'has' : ''}`}>
      <b>{value}</b>
      <span>{label}</span>
    </div>
  )
}
