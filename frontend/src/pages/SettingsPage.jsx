import { useEffect, useState } from 'react'
import { Me } from '../api'
import { askNotifPermission, notifPermission, playChime } from '../reminders'
import { ErrorNote } from '../components/ui.jsx'

const ALERTS = [
  [0, 'Tidak usah'],
  [1, '1 jam sebelum deadline'],
  [3, '3 jam sebelum deadline'],
  [6, '6 jam sebelum deadline'],
  [12, '12 jam sebelum deadline'],
  [24, '1 hari sebelum deadline'],
]

export default function SettingsPage({ settings, onSaved, onTest, notify }) {
  const [form, setForm] = useState(settings)
  const [perm, setPerm] = useState(notifPermission())
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  useEffect(() => setForm(settings), [settings])
  if (!form) return <p className="muted center">Memuat…</p>

  const dirty = JSON.stringify(form) !== JSON.stringify(settings)
  const set = (k, v) => setForm({ ...form, [k]: v })

  const save = async (e) => {
    e.preventDefault()
    setError('')
    if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(form.reminder_time)) return setError('Isi jam pengingat dengan benar.')
    setBusy(true)
    try {
      const saved = await Me.saveSettings({ ...form, deadline_alert_hours: Number(form.deadline_alert_hours) })
      onSaved(saved)
      notify('Pengaturan pengingat tersimpan.')
    } catch (err) { setError(err.message) }
    setBusy(false)
  }
  const allow = async () => setPerm(await askNotifPermission())

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Pengingat</h1>
          <p className="muted">Atur kapan SmartTask mengingatkanmu mengerjakan tugas.</p>
        </div>
      </div>

      <form className="panel settings" onSubmit={save} noValidate>
        <section>
          <div className="row">
            <div>
              <h2>Pengingat harian</h2>
              <p className="muted">Setiap hari pada jam yang kamu pilih, muncul ringkasan tugas yang belum selesai.</p>
            </div>
            <Switch checked={form.reminder_enabled} onChange={(v) => set('reminder_enabled', v)} label="Pengingat harian" />
          </div>
          <label className={`field inline ${form.reminder_enabled ? '' : 'off'}`}>
            <span className="field-label">Ingatkan setiap hari pukul</span>
            <input type="time" value={form.reminder_time} disabled={!form.reminder_enabled} onChange={(e) => set('reminder_time', e.target.value)} />
          </label>
        </section>

        <section>
          <h2>Peringatan sebelum deadline</h2>
          <p className="muted">Pengingat tambahan sekali untuk tiap tugas yang belum selesai.</p>
          <label className="field">
            <select value={form.deadline_alert_hours} onChange={(e) => set('deadline_alert_hours', Number(e.target.value))}>
              {ALERTS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
            </select>
          </label>
        </section>

        <section>
          <div className="row">
            <div>
              <h2>Bunyi</h2>
              <p className="muted">Bunyi “ting” saat pengingat muncul.</p>
            </div>
            <Switch checked={form.reminder_sound} onChange={(v) => set('reminder_sound', v)} label="Bunyi pengingat" />
          </div>
          <button type="button" className="btn sm" onClick={playChime}>🔊 Coba bunyi</button>
        </section>

        <section>
          <h2>Notifikasi browser</h2>
          <p className="muted">Agar pengingat juga muncul sebagai notifikasi di layar, izinkan notifikasi untuk situs ini.</p>
          {perm === 'granted' && <p className="ok-text">✓ Notifikasi sudah diizinkan.</p>}
          {perm === 'default' && <button type="button" className="btn sm" onClick={allow}>Izinkan notifikasi</button>}
          {perm === 'denied' && <p className="muted">Notifikasi diblokir. Buka pengaturan situs di browser (ikon gembok di address bar) lalu ubah ke “Izinkan”.</p>}
          {perm === 'unsupported' && <p className="muted">Browser ini tidak mendukung notifikasi. Pengingat tetap tampil di dalam halaman.</p>}
        </section>

        <p className="note">
          Pengingat berjalan selama SmartTask terbuka di browser (boleh di tab latar belakang). Jika baru dibuka setelah jam pengingat lewat,
          ringkasan hari ini langsung ditampilkan.
        </p>
        <ErrorNote>{error}</ErrorNote>
        <div className="modal-actions left">
          <button className="btn primary" disabled={busy || !dirty}>{busy ? 'Menyimpan…' : 'Simpan pengaturan'}</button>
          <button type="button" className="btn" onClick={onTest}>Kirim tes pengingat</button>
        </div>
      </form>
    </>
  )
}

function Switch({ checked, onChange, label }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} className={`switch ${checked ? 'on' : ''}`} onClick={() => onChange(!checked)}>
      <i />
    </button>
  )
}
