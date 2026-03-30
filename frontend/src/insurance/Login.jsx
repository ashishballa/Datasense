import { useState, useEffect, useRef } from 'react'
import { login, register } from './api'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const PASSWORD_RULES = [
  { label: '8+ characters', test: p => p.length >= 8 },
  { label: 'Uppercase letter', test: p => /[A-Z]/.test(p) },
  { label: 'Number', test: p => /\d/.test(p) },
  { label: 'Special character', test: p => /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(p) },
]

export default function Login({ onLogin }) {
  useEffect(() => { fetch(`${API}/`).catch(() => {}) }, [])

  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [slow, setSlow] = useState(false)
  const [usernameStatus, setUsernameStatus] = useState(null) // null | 'checking' | 'available' | 'taken'
  const debounceRef = useRef(null)

  // Check username availability with debounce (register mode only)
  useEffect(() => {
    if (mode !== 'register' || username.length < 3) {
      setUsernameStatus(null)
      return
    }
    setUsernameStatus('checking')
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/insurance/auth/check-username/${encodeURIComponent(username)}`)
        if (!res.ok) { setUsernameStatus(null); return }
        const data = await res.json()
        setUsernameStatus(data.available === true ? 'available' : 'taken')
      } catch {
        setUsernameStatus(null)
      }
    }, 500)
    return () => clearTimeout(debounceRef.current)
  }, [username, mode])

  const passwordRules = PASSWORD_RULES.map(r => ({ ...r, pass: r.test(password) }))
  const passwordValid = passwordRules.every(r => r.pass)
  const canSubmit = !loading && username && password &&
    (mode === 'login' || (passwordValid && usernameStatus !== 'taken' && usernameStatus !== 'checking'))

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSlow(false)
    setLoading(true)
    const slowTimer = setTimeout(() => setSlow(true), 5000)
    try {
      if (mode === 'register') await register(username, password)
      const data = await login(username, password)
      onLogin(data.access_token, username, data.role || 'user')
    } catch (err) {
      setError(err.message)
    } finally {
      clearTimeout(slowTimer)
      setSlow(false)
      setLoading(false)
    }
  }

  return (
    <div className="ins-login">
      <h2>Home Insurance</h2>
      <p className="ins-login-sub">Sign in to access the insurance assistant</p>
      <div className="ins-tabs">
        <button className={mode === 'login' ? 'active' : ''} onClick={() => { setMode('login'); setError(null) }}>Sign In</button>
        <button className={mode === 'register' ? 'active' : ''} onClick={() => { setMode('register'); setError(null) }}>Register</button>
      </div>
      <form onSubmit={handleSubmit} className="ins-login-form">
        <div className="ins-input-wrap">
          <input
            placeholder="Username"
            value={username}
            onChange={e => setUsername(e.target.value.trim())}
            disabled={loading}
            autoFocus
          />
          {mode === 'register' && username.length >= 3 && (
            <span className={`ins-username-status ${usernameStatus}`}>
              {usernameStatus === 'checking' && '…'}
              {usernameStatus === 'available' && '✓ Available'}
              {usernameStatus === 'taken' && '✗ Taken'}
            </span>
          )}
        </div>

        <div className="ins-input-wrap">
          <input
            type={showPassword ? 'text' : 'password'}
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            disabled={loading}
          />
          <button type="button" className="ins-show-pwd" onClick={() => setShowPassword(s => !s)}>
            {showPassword ? 'Hide' : 'Show'}
          </button>
        </div>

        {/* Password rules — only show in register mode when typing */}
        {mode === 'register' && password.length > 0 && (
          <div className="ins-pwd-rules">
            {passwordRules.map(r => (
              <span key={r.label} className={`ins-pwd-rule ${r.pass ? 'pass' : 'fail'}`}>
                {r.pass ? '✓' : '✗'} {r.label}
              </span>
            ))}
          </div>
        )}

        {error && <p className="ins-error">{error}</p>}
        <button type="submit" disabled={!canSubmit}>
          {loading ? (slow ? 'Server waking up… (~30s)' : 'Please wait…') : mode === 'login' ? 'Sign In' : 'Create Account'}
        </button>
      </form>
    </div>
  )
}
