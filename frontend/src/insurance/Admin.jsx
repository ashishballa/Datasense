import { useState, useEffect } from 'react'

export default function Admin({ token, onBack }) {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('http://localhost:8000/insurance/admin/stats', {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => r.json())
      .then(setStats)
      .catch(() => setError('Failed to load stats'))
  }, [token])

  if (error) return <div className="adm-wrap"><p className="ins-error">{error}</p></div>
  if (!stats) return <div className="adm-wrap"><p className="adm-loading">Loading…</p></div>

  const { totals, users, daily_questions } = stats
  const maxQ = Math.max(...daily_questions.map(d => d.questions), 1)

  return (
    <div className="adm-wrap">
      <div className="adm-header">
        <h2>Admin Dashboard</h2>
        <button onClick={onBack} className="ins-btn-secondary">Back</button>
      </div>

      {/* Stat cards */}
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

      {/* 7-day activity bar chart */}
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
  )
}
