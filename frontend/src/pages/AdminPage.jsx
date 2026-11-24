import { useCallback, useEffect, useMemo, useState } from 'react'
import { Admin } from '../api'
import { ConfirmDialog, ErrorNote, Field, Modal } from '../components/ui.jsx'

const dtFmt = new Intl.DateTimeFormat('id-ID', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })
const fmt = (iso) => (iso ? dtFmt.format(new Date(iso)).replace(/\./g, ':').replace(/ pukul/, '') : '—')
function ago(iso) {
  if (!iso) return 'Belum pernah'
  const m = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (m < 2) return 'Baru saja'
  if (m < 60) return `${m} menit lalu`
  if (m < 1440) return `${Math.round(m / 60)} jam lalu`
  return `${Math.round(m / 1440)} hari lalu`
}

export default function AdminPage({ me, notify }) {
  const [users, setUsers] = useState(null)
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [q, setQ] = useState('')
  const [filter, setFilter] = useState('all')
  const [reset, setReset] = useState(null)
  const [del, setDel] = useState(null)

  const load = useCallback(async () => {
    try {
      const [u, s] = await Promise.all([Admin.users(), Admin.stats()])
      setUsers(u); setStats(s); setError('')
    } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load() }, [load])

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase()
    return (users || []).filter((u) =>
      (!needle || u.name.toLowerCase().includes(needle) || u.email.toLowerCase().includes(needle)) &&
      (filter === 'all' || (filter === 'active' ? u.is_active : !u.is_active)))
  }, [users, q, filter])

  const toggle = async (u) => {
    try {
      await Admin.setActive(u.id, !u.is_active)
      notify(u.is_active ? `Akun ${u.name} dinonaktifkan.` : `Akun ${u.name} diaktifkan kembali.`)
      load()
    } catch (e) { notify(e.message, 'err') }
  }
  const remove = async () => {
    const u = del; setDel(null)
    try { await Admin.remove(u.id); notify(`Akun ${u.name} dihapus.`); load() } catch (e) { notify(e.message, 'err') }
  }

  if (error && !users) return <div className="error-note">{error}</div>
  if (!users) return <p className="muted center">Memuat…</p>

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Pantau Akun</h1>
          <p className="muted">Admin hanya melihat data akun dan jumlah aktivitas, bukan isi tugas pengguna.</p>
        </div>
        <button className="btn" onClick={load}>↻ Segarkan</button>
      </div>

      {stats && (
        <div className="stats six">
          <Stat label="Total akun" value={stats.total_users} />
          <Stat label="Akun aktif" value={stats.active_users} tone="done" />
          <Stat label="Nonaktif" value={stats.inactive_users} tone={stats.inactive_users ? 'late' : ''} />
          <Stat label="Masuk 24 jam terakhir" value={stats.active_last_24h} />
          <Stat label="Daftar 7 hari terakhir" value={stats.new_last_7_days} />
          <Stat label="Tugas selesai / total" value={`${stats.done_tasks}/${stats.total_tasks}`} />
        </div>
      )}

      <div className="filters">
        <input className="search" type="search" placeholder="Cari nama atau email…" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Cari akun" />
        <div className="chips" role="group" aria-label="Filter status">
          {[['all', 'Semua'], ['active', 'Aktif'], ['inactive', 'Nonaktif']].map(([k, l]) => (
            <button key={k} className={`chip ${filter === k ? 'on' : ''}`} onClick={() => setFilter(k)}>{l}</button>
          ))}
        </div>
      </div>

      <div className="tablewrap">
        <table className="table">
          <thead>
            <tr><th>Akun</th><th>Peran</th><th>Status</th><th>Terakhir masuk</th><th className="num">Matkul</th><th className="num">Tugas</th><th /></tr>
          </thead>
          <tbody>
            {shown.length === 0 && <tr><td colSpan={7} className="muted center-cell">Tidak ada akun yang cocok.</td></tr>}
            {shown.map((u) => (
              <tr key={u.id} className={u.is_active ? '' : 'inactive'}>
                <td data-label="Akun">
                  <b>{u.name}</b>{u.id === me.id && <small className="muted"> (Anda)</small>}
                  <div className="muted small">{u.email}</div>
                  <div className="muted small">Daftar {fmt(u.created_at)}</div>
                </td>
                <td data-label="Peran">{u.role === 'admin' ? 'Admin' : 'Mahasiswa'}</td>
                <td data-label="Status"><span className={`badge ${u.is_active ? 'ok' : 'late'}`}>{u.is_active ? 'Aktif' : 'Nonaktif'}</span></td>
                <td data-label="Terakhir masuk" title={fmt(u.last_login_at)}>{ago(u.last_login_at)}</td>
                <td data-label="Matkul" className="num">{u.course_count}</td>
                <td data-label="Tugas" className="num">{u.open_task_count} <span className="muted small">/ {u.task_count}</span></td>
                <td className="row-actions">
                  <button className="btn ghost sm" onClick={() => setReset(u)}>Reset password</button>
                  <button className="btn ghost sm" disabled={u.id === me.id} onClick={() => toggle(u)}>{u.is_active ? 'Nonaktifkan' : 'Aktifkan'}</button>
                  <button className="btn ghost sm danger-text" disabled={u.role === 'admin'} onClick={() => setDel(u)}>Hapus</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted small" style={{ marginTop: '.6rem' }}>Kolom “Tugas”: belum selesai / total.</p>

      {reset && <ResetForm user={reset} onClose={() => setReset(null)} onDone={() => { setReset(null); notify('Password diatur ulang.') }} />}
      {del && (
        <ConfirmDialog
          title="Hapus akun?"
          message={`Akun ${del.name} (${del.email}) beserta ${del.course_count} mata kuliah dan ${del.task_count} tugasnya akan dihapus permanen. Jika hanya ingin memblokir login, gunakan “Nonaktifkan”.`}
          confirmLabel="Hapus akun"
          onConfirm={remove}
          onClose={() => setDel(null)}
        />
      )}
    </>
  )
}

function Stat({ label, value, tone }) {
  return <div className={`stat ${tone || ''} has`}><b>{value}</b><span>{label}</span></div>
}

function ResetForm({ user, onClose, onDone }) {
  const [pw, setPw] = useState('')
  const [error, setError] = useState('')
  const submit = async (e) => {
    e.preventDefault()
    if (pw.length < 8) return setError('Password baru minimal 8 karakter.')
    try { await Admin.resetPassword(user.id, pw); onDone() } catch (err) { setError(err.message) }
  }
  return (
    <Modal title={`Reset password — ${user.name}`} onClose={onClose}>
      <form onSubmit={submit} noValidate>
        <Field label="Password baru" hint="Sampaikan password ini kepada pengguna secara langsung.">
          <input type="text" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="off" />
        </Field>
        <ErrorNote>{error}</ErrorNote>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>Batal</button>
          <button className="btn primary">Atur ulang</button>
        </div>
      </form>
    </Modal>
  )
}
