export const STATUS = [
  { value: 'todo', label: 'Belum dikerjakan', short: 'Belum' },
  { value: 'doing', label: 'Sedang dikerjakan', short: 'Dikerjakan' },
  { value: 'done', label: 'Selesai', short: 'Selesai' },
]

export const COURSE_COLORS = ['#4338ca', '#0891b2', '#059669', '#d97706', '#dc2626', '#c026d3', '#475569']

const dateFmt = new Intl.DateTimeFormat('id-ID', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
const timeFmt = new Intl.DateTimeFormat('id-ID', { hour: '2-digit', minute: '2-digit', hour12: false })

export const formatDeadline = (iso) => {
  const d = new Date(iso)
  return `${dateFmt.format(d)} · ${timeFmt.format(d).replace('.', ':')}`
}

// "2 hari lagi", "5 jam lagi", "terlambat 3 jam" ...
export function relativeDeadline(iso, now = Date.now()) {
  const diff = new Date(iso).getTime() - now
  const abs = Math.abs(diff)
  const min = Math.round(abs / 60000)
  const hr = Math.round(abs / 3600000)
  const day = Math.round(abs / 86400000)
  let txt
  if (min < 1) txt = 'sekarang'
  else if (min < 60) txt = `${min} menit`
  else if (hr < 24) txt = `${hr} jam`
  else txt = `${day} hari`
  if (txt === 'sekarang') return 'tepat sekarang'
  return diff < 0 ? `terlambat ${txt}` : `${txt} lagi`
}

// datetime-local (waktu lokal browser) <-> ISO UTC
export const toLocalInput = (iso) => {
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
export const fromLocalInput = (v) => new Date(v).toISOString()
export const defaultDeadlineInput = () => {
  const d = new Date(Date.now() + 24 * 3600 * 1000)
  d.setMinutes(0, 0, 0)
  return toLocalInput(d.toISOString())
}
