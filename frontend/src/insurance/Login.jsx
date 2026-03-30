import { useState, useEffect } from 'react'
import { login, register } from './api'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Login({ onLogin }) {
  // ping the backend on mount so Render wakes up before the user submits
  useEffect(() => { fetch(`${API}/`).catch(() => {}) }, [])
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [slow, setSlow] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setSlow(false)
    setLoading(true)
    const slowTimer = setTimeout(() => setSlow(true), 5000)
    try {
      if (mode === 'register') {
        await register(username, password)
      }
      const data = await login(username, password)
      onLogin(data.access_token, username)
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
        <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Sign In</button>
        <button className={mode === 'register' ? 'active' : ''} onClick={() => setMode('register')}>Register</button>
      </div>
      <form onSubmit={handleSubmit} className="ins-login-form">
        <input
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          disabled={loading}
          autoFocus
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          disabled={loading}
        />
        {error && <p className="ins-error">{error}</p>}
        <button type="submit" disabled={loading || !username || !password}>
          {loading ? (slow ? 'Server waking up… (~30s)' : 'Please wait…') : mode === 'login' ? 'Sign In' : 'Create Account & Sign In'}
        </button>
      </form>
    </div>
  )
}
