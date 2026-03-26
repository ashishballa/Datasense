import { useState } from 'react'

export default function App() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!question.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      if (!res.ok) {
        const body = await res.json()
        throw new Error(body.detail || `Server error: ${res.status}`)
      }
      setResult(await res.json())
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const columns = result?.rows?.length ? Object.keys(result.rows[0]) : []

  return (
    <div className="container">
      <h1>DataSense</h1>
      <p className="subtitle">Ask questions about your data in plain English</p>

      <form onSubmit={handleSubmit}>
        <div className="input-row">
          <input
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Which customer spent the most?"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? 'Thinking…' : 'Ask'}
          </button>
        </div>
      </form>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result">
          <p className="answer">{result.answer}</p>

          {columns.length > 0 && (
            <table>
              <thead>
                <tr>{columns.map(c => <th key={c}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {result.rows.map((row, i) => (
                  <tr key={i}>
                    {columns.map(c => <td key={c}>{row[c]}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <details>
            <summary>SQL</summary>
            <pre>{result.sql}</pre>
          </details>
        </div>
      )}
    </div>
  )
}
