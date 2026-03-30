import { useState, useEffect } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const EVENT_LABELS = {
  login: { label: 'Signed in', color: '#86efac' },
  login_failed: { label: 'Failed login', color: '#f87171' },
  register: { label: 'Registered', color: '#a5b4fc' },
  chat: { label: 'Chat message', color: '#67e8f9' },
  certificate_generated: { label: 'Certificate', color: '#fcd34d' },
  login_blocked: { label: 'Blocked', color: '#f87171' },
  role_changed: { label: 'Role changed', color: '#fb923c' },
}

function useAdminFetch(token, path) {
  return (method = 'GET', body = null) =>
    fetch(`${API}/insurance${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : null,
    })
}

export default function Admin({ token, onBack }) {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)
  const [users, setUsers] = useState(null)
  const [tab, setTab] = useState('stats') // 'stats' | 'users'
  const [roleMsg, setRoleMsg] = useState(null)

  const adminFetch = useAdminFetch(token, '')

  function loadStats() {
    fetch(`${API}/insurance/admin/stats`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (!r.ok) throw new Error(r.status); return r.json() })
      .then(setStats)
      .catch(() => setError('Failed to load stats — are you an admin?'))
  }

  function loadUsers() {
    fetch(`${API}/insurance/admin/users`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => setUsers(d.users))
      .catch(() => {})
  }

  useEffect(() => {
    loadStats()
    loadUsers()
    const interval = setInterval(loadStats, 30000)
    return () => clearInterval(interval)
  }, [token])

  async function changeRole(username, newRole) {
    const res = await fetch(`${API}/insurance/admin/users/${encodeURIComponent(username)}/role`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ role: newRole }),
    })
    if (res.ok) {
      setRoleMsg(`${username} is now ${newRole}`)
      loadUsers()
      setTimeout(() => setRoleMsg(null), 3000)
    }
  }

  if (error) return <div className="adm-wrap"><p className="ins-error">{error}</p><button onClick={onBack} className="ins-btn-secondary">Back</button></div>
  if (!stats) return <div className="adm-wrap"><p className="adm-loading">Loading…</p></div>

  const { totals, daily_questions = [], activity = [] } = stats
  const maxQ = Math.max(...daily_questions.map(d => d.questions), 1)

  return (
    <div className="adm-wrap">
      <div className="adm-header">
        <h2>Admin Dashboard</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={() => setTab('stats')} className={tab === 'stats' ? 'ins-btn-primary' : 'ins-btn-secondary'}>Stats</button>
          <button onClick={() => setTab('users')} className={tab === 'users' ? 'ins-btn-primary' : 'ins-btn-secondary'}>Users</button>
          <button onClick={onBack} className="ins-btn-secondary">Back</button>
        </div>
      </div>

      {tab === 'stats' && <>
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

          <div className="adm-section">
            <h3>Top Users</h3>
            <table className="adm-table">
              <thead>
                <tr><th>Username</th><th>Sessions</th><th>Questions</th><th>Joined</th></tr>
              </thead>
              <tbody>
                {stats.users.map(u => (
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
      </>}

      {tab === 'users' && (
        <div className="adm-section">
          <h3>User Management</h3>
          {roleMsg && <p className="ins-success" style={{ marginBottom: 12 }}>{roleMsg}</p>}
          {!users ? <p className="adm-loading">Loading…</p> : (
            <table className="adm-table">
              <thead>
                <tr><th>Username</th><th>Role</th><th>Sessions</th><th>Questions</th><th>Joined</th><th>Action</th></tr>
              </thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.username}>
                    <td>{u.username}</td>
                    <td><span style={{ color: u.role === 'admin' ? '#a5b4fc' : '#888' }}>{u.role}</span></td>
                    <td>{u.sessions}</td>
                    <td>{u.questions}</td>
                    <td>{new Date(u.created_at).toLocaleDateString()}</td>
                    <td>
                      {u.role === 'user'
                        ? <button className="ins-btn-primary" style={{ padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => changeRole(u.username, 'admin')}>Make Admin</button>
                        : <button className="ins-btn-secondary" style={{ padding: '4px 10px', fontSize: '0.78rem' }} onClick={() => changeRole(u.username, 'user')}>Remove Admin</button>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  )
}
