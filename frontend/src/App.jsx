import { useCallback, useEffect, useState } from 'react'
import { Auth, Me, getToken, setToken, setUnauthorizedHandler } from './api'
import AuthPage from './pages/AuthPage.jsx'
import TasksPage from './pages/TasksPage.jsx'
import CoursesPage from './pages/CoursesPage.jsx'
import AdminPage from './pages/AdminPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'
import ReminderEngine from './components/ReminderEngine.jsx'
import { Logo } from './components/ui.jsx'

const routeFromHash = () => (window.location.hash.replace('#/', '') || 'tugas').split('?')[0]

export default function App() {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(!!getToken())
  const [route, setRoute] = useState(routeFromHash())
  const [toast, setToast] = useState(null)
  const [settings, setSettings] = useState(null)
  const [testSignal, setTestSignal] = useState(0)

  const notify = useCallback((msg, kind = 'ok') => {
    setToast({ msg, kind, id: Date.now() })
  }, [])
  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 3500)
    return () => clearTimeout(t)
  }, [toast])

  const signOut = useCallback((silent) => {
    setToken(null)
    setUser(null)
    setSettings(null)
    if (!silent) window.location.hash = '#/tugas'
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      signOut(true)
      notify('Sesi berakhir, silakan masuk lagi.', 'err')
    })
    const onHash = () => setRoute(routeFromHash())
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [signOut, notify])

  useEffect(() => {
    if (!getToken()) return
    Auth.me().then(setUser).catch(() => setToken(null)).finally(() => setBooting(false))
  }, [])

  useEffect(() => {
    if (user) Me.settings().then(setSettings).catch(() => {})
  }, [user])

  const onAuthed = ({ access_token, user }) => {
    setToken(access_token)
    setUser(user)
    window.location.hash = '#/tugas'
  }

  const logout = async () => {
    try { await Auth.logout() } catch { /* token mungkin sudah tidak berlaku */ }
    signOut()
  }

  if (booting) return <div className="boot"><Logo /></div>
  if (!user) return (<><AuthPage onAuthed={onAuthed} />{toast && <Toast t={toast} />}</>)

  const isAdmin = user.role === 'admin'
  const page = route === 'admin' && !isAdmin ? 'tugas' : route
  const nav = [
    ['tugas', 'Tugas'],
    ['matkul', 'Mata Kuliah'],
    ['pengingat', 'Pengingat'],
    ...(isAdmin ? [['admin', 'Admin']] : []),
  ]

  return (
    <div className="app">
      <header className="topbar">
        <a className="brand" href="#/tugas"><Logo /></a>
        <nav className="nav" aria-label="Navigasi utama">
          {nav.map(([key, label]) => (
            <a key={key} href={`#/${key}`} className={page === key ? 'active' : ''} aria-current={page === key ? 'page' : undefined}>{label}</a>
          ))}
        </nav>
        <div className="who">
          <span className="who-name" title={user.email}>{user.name}</span>
          <button className="btn ghost sm" onClick={logout}>Keluar</button>
        </div>
      </header>
      <main className="content">
        {page === 'matkul' ? <CoursesPage notify={notify} />
          : page === 'pengingat' ? <SettingsPage settings={settings} onSaved={setSettings} onTest={() => setTestSignal((n) => n + 1)} notify={notify} />
          : page === 'admin' ? <AdminPage me={user} notify={notify} />
          : <TasksPage user={user} notify={notify} />}
      </main>
      {settings && <ReminderEngine userId={user.id} settings={settings} testSignal={testSignal} />}
      {toast && <Toast t={toast} />}
    </div>
  )
}

function Toast({ t }) {
  return <div key={t.id} className={`toast ${t.kind}`} role="status">{t.msg}</div>
}
