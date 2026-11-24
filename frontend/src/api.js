// Klien API tipis. Token JWT disimpan di localStorage dan dikirim lewat header Authorization.
const KEY = 'smarttask.token'
let onUnauthorized = () => {}

export const setUnauthorizedHandler = (fn) => (onUnauthorized = fn)
export const getToken = () => {
  try { return localStorage.getItem(KEY) } catch { return null }
}
export const setToken = (t) => {
  try { t ? localStorage.setItem(KEY, t) : localStorage.removeItem(KEY) } catch { /* abaikan */ }
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

function messageFrom(body, status) {
  const d = body?.detail
  if (typeof d === 'string') return d
  if (Array.isArray(d) && d.length) {
    // galat validasi pydantic -> pesan ramah
    const f = d[0]
    const field = f.loc?.[f.loc.length - 1]
    const labels = { name: 'Nama', email: 'Email', password: 'Password', title: 'Nama tugas', deadline: 'Deadline', course_id: 'Mata kuliah', new_password: 'Password baru', reminder_time: 'Jam pengingat' }
    return `${labels[field] || field || 'Input'}: ${f.msg?.replace('Value error, ', '') || 'tidak valid'}`
  }
  return `Terjadi kesalahan (${status}).`
}

export async function api(path, { method = 'GET', body, auth = true } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getToken()
  if (auth && token) headers.Authorization = `Bearer ${token}`
  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined })
  } catch {
    throw new ApiError('Tidak dapat terhubung ke server. Periksa koneksi internet Anda.', 0)
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    if (res.status === 401 && auth && token) onUnauthorized()
    throw new ApiError(messageFrom(data, res.status), res.status)
  }
  return data
}

export const Auth = {
  register: (b) => api('/auth/register', { method: 'POST', body: b, auth: false }),
  login: (b) => api('/auth/login', { method: 'POST', body: b, auth: false }),
  me: () => api('/auth/me'),
  logout: () => api('/auth/logout', { method: 'POST' }),
}
export const Courses = {
  list: () => api('/courses'),
  create: (b) => api('/courses', { method: 'POST', body: b }),
  update: (id, b) => api(`/courses/${id}`, { method: 'PUT', body: b }),
  remove: (id) => api(`/courses/${id}`, { method: 'DELETE' }),
}
export const Tasks = {
  list: (params = {}) => {
    const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== '' && v != null)).toString()
    return api(`/tasks${q ? `?${q}` : ''}`)
  },
  create: (b) => api('/tasks', { method: 'POST', body: b }),
  update: (id, b) => api(`/tasks/${id}`, { method: 'PATCH', body: b }),
  setStatus: (id, status) => api(`/tasks/${id}/status`, { method: 'PATCH', body: { status } }),
  remove: (id) => api(`/tasks/${id}`, { method: 'DELETE' }),
}
export const Me = {
  settings: () => api('/me/settings'),
  saveSettings: (b) => api('/me/settings', { method: 'PUT', body: b }),
}
export const Admin = {
  stats: () => api('/admin/stats'),
  remove: (id) => api(`/admin/users/${id}`, { method: 'DELETE' }),
  users: () => api('/admin/users'),
  setActive: (id, is_active) => api(`/admin/users/${id}`, { method: 'PATCH', body: { is_active } }),
  resetPassword: (id, new_password) => api(`/admin/users/${id}/reset-password`, { method: 'POST', body: { new_password } }),
}
