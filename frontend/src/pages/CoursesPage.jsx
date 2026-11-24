import { useCallback, useEffect, useState } from 'react'
import { Courses } from '../api'
import { COURSE_COLORS } from '../utils'
import { ConfirmDialog, Empty, ErrorNote, Field, Modal } from '../components/ui.jsx'

export default function CoursesPage({ notify }) {
  const [courses, setCourses] = useState(null)
  const [editing, setEditing] = useState(null) // null | {} (baru) | course
  const [toDelete, setToDelete] = useState(null)
  const [loadError, setLoadError] = useState('')

  const load = useCallback(() => Courses.list().then(setCourses).catch((e) => setLoadError(e.message)), [])
  useEffect(() => { load() }, [load])

  const remove = async () => {
    const c = toDelete
    setToDelete(null)
    try { await Courses.remove(c.id); notify('Mata kuliah dihapus.'); load() } catch (e) { notify(e.message, 'err') }
  }

  if (loadError) return <div className="error-note">{loadError}</div>
  if (!courses) return <p className="muted center">Memuat…</p>

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Mata Kuliah</h1>
          <p className="muted">Kelompokkan tugas berdasarkan mata kuliah semester ini.</p>
        </div>
        <button className="btn primary fab" onClick={() => setEditing({})}><span aria-hidden="true">＋</span> Mata kuliah</button>
      </div>

      {courses.length === 0 ? (
        <Empty title="Belum ada mata kuliah">Tambahkan mata kuliah pertamamu, misalnya “Komputasi Awan”.</Empty>
      ) : (
        <ul className="courselist">
          {courses.map((c) => (
            <li key={c.id} className="course" style={{ '--course': c.color }}>
              <span className="swatch" />
              <div className="course-main">
                <h3>{c.name}</h3>
                <p className="muted">{c.task_count} tugas · {c.open_task_count} belum selesai</p>
              </div>
              <div className="task-actions">
                <button className="btn ghost sm" onClick={() => setEditing(c)}>Ubah</button>
                <button className="btn ghost sm danger-text" onClick={() => setToDelete(c)}>Hapus</button>
              </div>
            </li>
          ))}
        </ul>
      )}

      {editing && (
        <CourseForm
          course={editing.id ? editing : null}
          nextColor={COURSE_COLORS[courses.length % COURSE_COLORS.length]}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); notify('Mata kuliah tersimpan.'); load() }}
        />
      )}
      {toDelete && (
        <ConfirmDialog
          title="Hapus mata kuliah?"
          message={toDelete.task_count ? `“${toDelete.name}” beserta ${toDelete.task_count} tugas di dalamnya akan dihapus permanen.` : `“${toDelete.name}” akan dihapus.`}
          onConfirm={remove}
          onClose={() => setToDelete(null)}
        />
      )}
    </>
  )
}

function CourseForm({ course, nextColor, onClose, onSaved }) {
  const [name, setName] = useState(course?.name ?? '')
  const [color, setColor] = useState(course?.color ?? nextColor)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return setError('Nama mata kuliah wajib diisi.')
    setBusy(true)
    try {
      course ? await Courses.update(course.id, { name, color }) : await Courses.create({ name, color })
      onSaved()
    } catch (err) { setError(err.message); setBusy(false) }
  }
  return (
    <Modal title={course ? 'Ubah mata kuliah' : 'Mata kuliah baru'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <Field label="Nama mata kuliah">
          <input value={name} onChange={(e) => setName(e.target.value)} maxLength={120} placeholder="mis. Komputasi Awan" />
        </Field>
        <div className="field">
          <span className="field-label">Warna penanda</span>
          <div className="swatches">
            {COURSE_COLORS.map((c) => (
              <button type="button" key={c} className={`sw ${c === color ? 'on' : ''}`} style={{ background: c }} onClick={() => setColor(c)} aria-label={`Warna ${c}`} aria-pressed={c === color} />
            ))}
          </div>
        </div>
        <ErrorNote>{error}</ErrorNote>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Batal</button>
          <button className="btn primary" disabled={busy}>{busy ? 'Menyimpan…' : 'Simpan'}</button>
        </div>
      </form>
    </Modal>
  )
}
