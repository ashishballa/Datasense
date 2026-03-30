import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const EVENT_LABELS = {
  login: { label: 'Signed in', color: '#86efac' },
  login_failed: { label: 'Failed login', color: '#f87171' },
  register: { label: 'Registered', color: '#a5b4fc' },
  chat: { label: 'Chat message', color: '#67e8f9' },
  certificate_generated: { label: 'Certificate', color: '#fcd34d' },
}

export default function Admin({ token, onBack }) {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/insurance/admin/stats`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setStats)
      .catch(() => setError('Failed to load stats'))

    // auto-refresh every 30s
    const interval = setInterval(() => {
      fetch(`${API}/insurance/admin/stats`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.json()).then(setStats).catch(() => {})
    }, 30000)
    return () => clearInterval(interval)
  }, [token])

  if (error) return <div className="adm-wrap"><p className="ins-error">{error}</p></div>
  if (!stats) return <div className="adm-wrap"><p className="adm-loading">Loading…</p></div>

  const { totals, users, daily_questions = [], activity = [] } = stats
  const maxQ = Math.max(...daily_questions.map(d => d.questions), 1)

  return (
    <div className="adm-wrap">
      <div className="adm-header">
        <h2>Admin Dashboard</h2>
        <button onClick={onBack} className="ins-btn-secondary">Back</button>
      </div>

      <div className="adm-cards">
        {[
          { label: 'Users', value: totals.users },
          { label: 'Sessions', value: totals.sessions },
          { label: 'Questions Asked', value: totals.messages },
          { label: 'Certificates', value: totals.certificates },
        ].map(c => (
          <div key={c.label} className="adm-card">
            <span className="adm-card-value">{c.value}</span>
            <span className="adm-card-label">{c.label}</span>
          </div>
        ))}
      </div>

      {daily_questions.length > 0 && (
        <div className="adm-section">
          <h3>Questions — Last 7 Days</h3>
          <div className="adm-chart">
            {daily_questions.map(d => (
              <div key={d.day} className="adm-bar-col">
                <span className="adm-bar-val">{d.questions}</span>
                <div className="adm-bar" style={{ height: `${(d.questions / maxQ) * 100}%` }} />
                <span className="adm-bar-label">{new Date(d.day).toLocaleDateString('en', { weekday: 'short' })}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="adm-two-col">
        {/* Activity feed */}
        <div className="adm-section">
          <h3>Activity Log <span className="adm-refresh-hint">auto-refreshes 30s</span></h3>
          <div className="adm-feed">
            {activity.length === 0 && <p className="adm-empty">No activity yet</p>}
            {activity.map(a => {
              const ev = EVENT_LABELS[a.event] || { label: a.event, color: '#888' }
              return (
                <div key={a.id} className="adm-feed-row">
                  <span className="adm-feed-badge" style={{ color: ev.color }}>{ev.label}</span>
                  <span className="adm-feed-user">{a.username || '—'}</span>
                  {a.detail && <span className="adm-feed-detail">{a.detail}</span>}
                  <span className="adm-feed-time">{new Date(a.created_at).toLocaleTimeString()}</span>
                </div>
              )
            })}
          </div>
        </div>

        {/* User table */}
        <div className="adm-section">
          <h3>Users</h3>
          <table className="adm-table">
            <thead>
              <tr><th>Username</th><th>Sessions</th><th>Questions</th><th>Joined</th></tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.username}>
                  <td>{u.username}</td>
                  <td>{u.sessions}</td>
                  <td>{u.questions}</td>
                  <td>{new Date(u.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
