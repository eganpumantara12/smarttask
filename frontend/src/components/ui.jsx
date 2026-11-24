import { useEffect, useRef } from 'react'

export function Logo({ size = 28 }) {
  return (
    <span className="logo">
      <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="16" fill="var(--accent)" />
        <circle cx="32" cy="32" r="21" fill="none" stroke="#fff" strokeWidth="4.5" />
        <path d="M32 15.5v2.6M32 45.9v2.6M15.5 32h2.6M45.9 32h2.6" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" opacity=".85" />
        <path d="M23.5 33l6 6 11.5-14" fill="none" stroke="#fff" strokeWidth="5.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <span>SmartTask</span>
    </span>
  )
}

export function Modal({ title, onClose, children }) {
  const ref = useRef(null)
  useEffect(() => {
    const prev = document.activeElement
    const onKey = (e) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    ref.current?.querySelector('input,select,textarea,button')?.focus()
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      prev?.focus?.()
    }
  }, [onClose])
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title} ref={ref}>
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Tutup">✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function Field({ label, children, hint }) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </label>
  )
}

export function ErrorNote({ children }) {
  if (!children) return null
  return <div className="error-note" role="alert">{children}</div>
}

export function Empty({ title, children }) {
  return (
    <div className="empty">
      <div className="empty-art" aria-hidden="true">☑</div>
      <strong>{title}</strong>
      <p>{children}</p>
    </div>
  )
}

export function ConfirmDialog({ title, message, confirmLabel = 'Hapus', onConfirm, onClose }) {
  return (
    <Modal title={title} onClose={onClose}>
      <p className="muted">{message}</p>
      <div className="modal-actions">
        <button className="btn ghost" onClick={onClose}>Batal</button>
        <button className="btn danger" onClick={onConfirm}>{confirmLabel}</button>
      </div>
    </Modal>
  )
}
