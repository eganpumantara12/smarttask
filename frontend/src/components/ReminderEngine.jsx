import { useCallback, useEffect, useRef, useState } from 'react'
import { Tasks } from '../api'
import { alertedSet, lastDaily, markDaily, playChime, saveAlerted, showSystemNotification, todayKey } from '../reminders'
import { relativeDeadline } from '../utils'

const CHECK_MS = 30 * 1000
const REFRESH_MS = 60 * 1000

// Berjalan selama SmartTask terbuka di browser: memeriksa jam pengingat harian dan batas waktu per tugas.
export default function ReminderEngine({ userId, settings, testSignal }) {
  const [items, setItems] = useState([])
  const tasksRef = useRef([])
  const loadedRef = useRef(false) // jangan memeriksa sebelum daftar tugas pertama selesai dimuat
  const settingsRef = useRef(settings)
  settingsRef.current = settings

  const push = useCallback((title, body, kind = 'daily') => {
    const s = settingsRef.current
    setItems((cur) => [...cur.slice(-2), { id: Date.now() + Math.random(), title, body, kind }])
    if (s?.reminder_sound) playChime()
    showSystemNotification(title, body)
  }, [])

  const summary = (tasks) => {
    const open = tasks.filter((t) => t.status !== 'done')
    if (!open.length) return null
    const late = open.filter((t) => t.is_overdue).length
    const next = open[0]
    return {
      title: `Waktunya mengerjakan tugas — ${open.length} belum selesai`,
      body: `${late ? `${late} terlambat. ` : ''}Terdekat: “${next.title}” (${next.course_name}), ${relativeDeadline(next.deadline)}.`,
    }
  }

  const check = useCallback(() => {
    const s = settingsRef.current
    if (!s || !loadedRef.current) return
    const tasks = tasksRef.current
    const now = new Date()

    if (s.reminder_enabled) {
      const [hh, mm] = s.reminder_time.split(':').map(Number)
      const due = hh * 60 + mm <= now.getHours() * 60 + now.getMinutes()
      if (due && lastDaily(userId) !== todayKey(now)) {
        const sm = summary(tasks)
        if (sm) {  // ditandai "sudah" hanya jika benar-benar ada tugas yang diingatkan
          markDaily(userId)
          push(sm.title, sm.body, 'daily')
        }
      }
    }

    if (s.deadline_alert_hours > 0) {
      const seen = alertedSet(userId)
      let changed = false
      for (const t of tasks) {
        if (t.status === 'done') continue
        const left = new Date(t.deadline).getTime() - now.getTime()
        const key = `${t.id}@${t.deadline}@${s.deadline_alert_hours}`
        if (left > 0 && left <= s.deadline_alert_hours * 3600e3 && !seen.has(key)) {
          seen.add(key)
          changed = true
          push(`Deadline mendekat: ${t.title}`, `${t.course_name} — ${relativeDeadline(t.deadline)}.`, 'deadline')
        }
      }
      if (changed) saveAlerted(userId, seen)
    }
  }, [userId, push])

  const refresh = useCallback(async () => {
    try {
      tasksRef.current = await Tasks.list()
      loadedRef.current = true
      check()
    } catch { /* jaringan putus: coba lagi pada siklus berikutnya */ }
  }, [check])

  useEffect(() => {
    refresh()
    const a = setInterval(refresh, REFRESH_MS)
    const b = setInterval(check, CHECK_MS)
    const onVisible = () => document.visibilityState === 'visible' && refresh()
    document.addEventListener('visibilitychange', onVisible)
    return () => { clearInterval(a); clearInterval(b); document.removeEventListener('visibilitychange', onVisible) }
  }, [refresh, check])

  // dipicu ulang saat pengaturan disimpan
  useEffect(() => { check() }, [settings, check])

  // tombol "Kirim tes pengingat" di halaman pengaturan
  useEffect(() => {
    if (!testSignal) return
    const sm = summary(tasksRef.current)
    push(sm?.title || 'Tes pengingat SmartTask', sm?.body || 'Pengingat berfungsi. Saat ada tugas belum selesai, ringkasannya muncul di sini.', 'test')
  }, [testSignal, push])

  if (!items.length) return null
  return (
    <div className="reminders" aria-live="polite">
      {items.map((it) => (
        <div key={it.id} className={`reminder ${it.kind}`} role="alert">
          <span className="bell" aria-hidden="true">🔔</span>
          <div>
            <strong>{it.title}</strong>
            <p>{it.body}</p>
            <a href="#/tugas" onClick={() => setItems((c) => c.filter((x) => x.id !== it.id))}>Lihat tugas</a>
          </div>
          <button className="icon-btn" aria-label="Tutup pengingat" onClick={() => setItems((c) => c.filter((x) => x.id !== it.id))}>✕</button>
        </div>
      ))}
    </div>
  )
}
