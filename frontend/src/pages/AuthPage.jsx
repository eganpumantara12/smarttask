import { useState } from 'react'
import { Auth } from '../api'
import { ErrorNote, Field, Logo } from '../components/ui.jsx'

const API_BASE_URL = (import.meta.env?.VITE_API_URL || '').replace(/\/+$/, '')

export default function AuthPage({ onAuthed }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [otpStep, setOtpStep] = useState(false)
  const [pendingEmail, setPendingEmail] = useState('')
  const [otpCode, setOtpCode] = useState('')
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  const isLogin = mode === 'login'

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setOtpStep(false)
    setError('')
    setInfo('')
  }

  const submitAuth = async (e) => {
    e.preventDefault()
    setError('')
    setInfo('')

    const cleanEmail = form.email.trim().toLowerCase()

    if (!isLogin && form.name.trim().length < 2) {
      return setError('Nama minimal 2 karakter.')
    }
    if (!cleanEmail) {
      return setError('Email wajib diisi.')
    }
    if (!isLogin && form.password.length < 8) {
      return setError('Password minimal 8 karakter.')
    }
    if (!form.password) {
      return setError('Password wajib diisi.')
    }

    setBusy(true)
    try {
      if (isLogin) {
        const res = await Auth.login({ email: cleanEmail, password: form.password })
        onAuthed(res)
      } else {
        await Auth.register({
          name: form.name.trim(),
          email: cleanEmail,
          password: form.password,
        })
        setPendingEmail(cleanEmail)
        setOtpCode('')
        setOtpStep(true)
        setInfo('Kode OTP 6 digit telah dikirim ke email Anda. Cek kotak masuk atau folder spam (berlaku 15 menit).')
      }
    } catch (err) {
      setError(err.message || 'Terjadi kesalahan.')
    } finally {
      setBusy(false)
    }
  }

  const handleVerifyOtp = async (e) => {
    e.preventDefault()
    setError('')
    setInfo('')

    const cleanEmail = (pendingEmail || form.email).trim().toLowerCase()
    const cleanOtp = otpCode.replace(/\D/g, '').trim()

    if (!cleanEmail) {
      return setError('Email wajib diisi.')
    }
    if (cleanOtp.length !== 6) {
      return setError('Masukkan 6 digit kode OTP.')
    }

    setBusy(true)
    try {
      const res = await fetch(`${API_BASE_URL}/api/auth/verify-email`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: cleanEmail,
          otp_code: cleanOtp,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        setError(data.detail || 'Verifikasi OTP gagal.')
        return
      }

      setOtpStep(false)
      setOtpCode('')
      setForm((prev) => ({ ...prev, email: cleanEmail, password: '' }))
      setMode('login')
      setInfo(data.message || 'Email berhasil diverifikasi! Silakan login dengan akun Anda.')
    } catch {
      setError('Gagal terhubung ke server saat memverifikasi OTP.')
    } finally {
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
        {!otpStep ? (
          <>
            <div className="tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={isLogin}
                className={isLogin ? 'on' : ''}
                onClick={() => switchMode('login')}
              >
                Masuk
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={!isLogin}
                className={!isLogin ? 'on' : ''}
                onClick={() => switchMode('register')}
              >
                Daftar
              </button>
            </div>

            {info && <div className="note" style={{ marginBottom: '1rem' }}>{info}</div>}

            <form onSubmit={submitAuth} noValidate>
              {!isLogin && (
                <Field label="Nama lengkap">
                  <input
                    value={form.name}
                    onChange={set('name')}
                    autoComplete="name"
                    placeholder="Nama lengkap Anda"
                  />
                </Field>
              )}

              <Field label="Email">
                <input
                  type="email"
                  value={form.email}
                  onChange={set('email')}
                  autoComplete="email"
                  inputMode="email"
                  placeholder="nama@email.com"
                />
              </Field>

              <Field label="Password" hint={isLogin ? undefined : 'Minimal 8 karakter.'}>
                <input
                  type="password"
                  value={form.password}
                  onChange={set('password')}
                  autoComplete={isLogin ? 'current-password' : 'new-password'}
                  placeholder="••••••••"
                />
              </Field>

              <ErrorNote>{error}</ErrorNote>

              <button className="btn primary block" disabled={busy}>
                {busy ? 'Memproses…' : isLogin ? 'Masuk' : 'Buat akun & kirim OTP'}
              </button>
            </form>
          </>
        ) : (
          <>
            <div style={{ marginBottom: '1rem' }}>
              <h2 style={{ fontSize: '1.2rem' }}>Verifikasi Kode OTP</h2>
              <p className="muted" style={{ fontSize: '.9rem', marginTop: '.25rem' }}>
                Dikirim ke <b>{pendingEmail || form.email}</b>
              </p>
            </div>

            {info && <div className="note" style={{ marginBottom: '1rem' }}>{info}</div>}

            <form onSubmit={handleVerifyOtp} noValidate>
              <Field label="Kode OTP (6 digit)" hint="Berlaku 15 menit.">
                <input
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="123456"
                  style={{
                    textAlign: 'center',
                    fontWeight: 700,
                    fontSize: '1.2rem',
                    letterSpacing: '0.35em',
                  }}
                />
              </Field>

              <ErrorNote>{error}</ErrorNote>

              <button className="btn primary block" disabled={busy}>
                {busy ? 'Memverifikasi…' : 'Verifikasi Email'}
              </button>

              <div style={{ display: 'flex', justifyContent: 'space-between', gap: '.5rem', marginTop: '.75rem' }}>
                <button
                  type="button"
                  className="btn ghost sm"
                  disabled={busy}
                  onClick={() => {
                    setOtpStep(false)
                    setMode('register')
                    setError('')
                  }}
                >
                  Ubah data / Kirim ulang OTP
                </button>
                <button
                  type="button"
                  className="btn ghost sm"
                  disabled={busy}
                  onClick={() => switchMode('login')}
                >
                  Ke halaman Masuk
                </button>
              </div>
            </form>
          </>
        )}
      </section>
    </div>
  )
}
