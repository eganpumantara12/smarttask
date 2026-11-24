// Utilitas pengingat: bunyi (Web Audio, tanpa file), notifikasi browser, dan penanda "sudah diingatkan".
let ctx
export function playChime() {
  try {
    ctx = ctx || new (window.AudioContext || window.webkitAudioContext)()
    if (ctx.state === 'suspended') ctx.resume()
    const now = ctx.currentTime
    ;[[880, 0], [1175, 0.18], [1568, 0.36]].forEach(([freq, at]) => {
      const o = ctx.createOscillator()
      const g = ctx.createGain()
      o.type = 'sine'
      o.frequency.value = freq
      g.gain.setValueAtTime(0.0001, now + at)
      g.gain.exponentialRampToValueAtTime(0.25, now + at + 0.02)
      g.gain.exponentialRampToValueAtTime(0.0001, now + at + 0.5)
      o.connect(g).connect(ctx.destination)
      o.start(now + at)
      o.stop(now + at + 0.55)
    })
  } catch { /* browser memblokir audio: abaikan, banner tetap tampil */ }
}

export const notifSupported = () => typeof window !== 'undefined' && 'Notification' in window
export const notifPermission = () => (notifSupported() ? Notification.permission : 'unsupported')
export const askNotifPermission = async () => (notifSupported() ? Notification.requestPermission() : 'unsupported')

export function showSystemNotification(title, body) {
  if (notifPermission() !== 'granted') return
  try {
    new Notification(title, { body, icon: '/favicon.svg', tag: 'smarttask' })
  } catch { /* beberapa browser HP butuh service worker: abaikan */ }
}

const read = (k, fallback) => {
  try { return JSON.parse(localStorage.getItem(k)) ?? fallback } catch { return fallback }
}
const write = (k, v) => {
  try { localStorage.setItem(k, JSON.stringify(v)) } catch { /* abaikan */ }
}
export const todayKey = (d = new Date()) => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`
export const lastDaily = (uid) => read(`smarttask.daily.${uid}`, '')
export const markDaily = (uid) => write(`smarttask.daily.${uid}`, todayKey())
export const alertedSet = (uid) => new Set(read(`smarttask.alerted.${uid}`, []))
export const saveAlerted = (uid, set) => write(`smarttask.alerted.${uid}`, [...set].slice(-300))
