import { useState } from 'react'
import { Auth } from '../api'
import { ErrorNote, Field, Logo } from '../components/ui.jsx'

export default function AuthPage({ onAuthed }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const isLogin = mode === 'login'

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (!isLogin && form.name.trim().length < 2) return setError('Nama minimal 2 karakter.')
    if (!form.email.trim()) return setError('Email wajib diisi.')
    if (!isLogin && form.password.length < 8) return setError('Password minimal 8 karakter.')
    if (!form.password) return setError('Password wajib diisi.')
    setBusy(true)
    try {
      const res = isLogin
        ? await Auth.login({ email: form.email.trim(), password: form.password })
        : await Auth.register({ name: form.name, email: form.email.trim(), password: form.password })
      onAuthed(res)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="auth">
      <section className="auth-hero">
        <Logo size={36} />
        <h1>Semua tugas kuliah, <em>satu tempat.</em></h1>
        <p>
          Berhenti mencari info tugas di WhatsApp, Google Classroom, dan catatan pribadi.
          Catat sekali, lihat urutan prioritas berdasarkan deadline dari HP maupun laptop.
        </p>
        <ul className="points">
          <li><b>Per mata kuliah</b> — kelompokkan dan filter dengan cepat</li>
          <li><b>Prioritas deadline</b> — yang paling mendesak selalu di atas</li>
          <li><b>Penanda terlambat</b> — tidak ada lagi tugas yang terlewat</li>
        </ul>
      </section>
      <section className="auth-card">
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={isLogin} className={isLogin ? 'on' : ''} onClick={() => { setMode('login'); setError('') }}>Masuk</button>
          <button role="tab" aria-selected={!isLogin} className={!isLogin ? 'on' : ''} onClick={() => { setMode('register'); setError('') }}>Daftar</button>
        </div>
        <form onSubmit={submit} noValidate>
          {!isLogin && (
            <Field label="Nama lengkap">
              <input value={form.name} onChange={set('name')} autoComplete="name" />
            </Field>
          )}
          <Field label="Email">
            <input type="email" value={form.email} onChange={set('email')} autoComplete="email" inputMode="email" />
          </Field>
          <Field label="Password" hint={isLogin ? undefined : 'Minimal 8 karakter.'}>
            <input type="password" value={form.password} onChange={set('password')} autoComplete={isLogin ? 'current-password' : 'new-password'} />
          </Field>
          <ErrorNote>{error}</ErrorNote>
          <button className="btn primary block" disabled={busy}>{busy ? 'Memproses…' : isLogin ? 'Masuk' : 'Buat akun'}</button>
        </form>
      </section>
    </div>
  )
}
