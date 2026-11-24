import { useState } from 'react'
import { Tasks } from '../api'
import { defaultDeadlineInput, fromLocalInput, toLocalInput } from '../utils'
import { ErrorNote, Field, Modal } from './ui.jsx'

export default function TaskForm({ task, courses, defaultCourseId, onSaved, onClose }) {
  const [title, setTitle] = useState(task?.title ?? '')
  const [courseId, setCourseId] = useState(task?.course_id ?? defaultCourseId ?? courses[0]?.id ?? '')
  const [description, setDescription] = useState(task?.description ?? '')
  const [deadline, setDeadline] = useState(task ? toLocalInput(task.deadline) : defaultDeadlineInput())
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!title.trim()) return setError('Nama tugas wajib diisi.')
    if (!courseId) return setError('Pilih mata kuliah terlebih dahulu.')
    if (!deadline || Number.isNaN(new Date(deadline).getTime())) return setError('Deadline wajib diisi.')
    setBusy(true)
    try {
      const body = { title, course_id: Number(courseId), description, deadline: fromLocalInput(deadline) }
      const saved = task ? await Tasks.update(task.id, body) : await Tasks.create(body)
      onSaved(saved, !task)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <Modal title={task ? 'Ubah tugas' : 'Tugas baru'} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <Field label="Nama tugas">
          <input value={title} onChange={(e) => setTitle(e.target.value)} maxLength={200} placeholder="mis. Laporan LKM 9" />
        </Field>
        <Field label="Mata kuliah">
          <select value={courseId} onChange={(e) => setCourseId(e.target.value)}>
            {courses.length === 0 && <option value="">— belum ada mata kuliah —</option>}
            {courses.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Deadline" hint="Waktu mengikuti zona waktu perangkat Anda.">
          <input type="datetime-local" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
        </Field>
        <Field label="Catatan (opsional)">
          <textarea rows={3} value={description} onChange={(e) => setDescription(e.target.value)} maxLength={2000} />
        </Field>
        <ErrorNote>{error}</ErrorNote>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Batal</button>
          <button className="btn primary" disabled={busy}>{busy ? 'Menyimpan…' : 'Simpan'}</button>
        </div>
      </form>
    </Modal>
  )
}
