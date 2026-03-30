const BASE = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/insurance`

function authHeaders(token) {
  return { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
}

async function parseError(res, fallback) {
  try {
    const body = await res.json()
    return body.detail || fallback
  } catch {
    return fallback
  }
}

export async function register(username, password) {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) throw new Error(await parseError(res, 'Registration failed'))
  return res.json()
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password }),
  })
  if (!res.ok) throw new Error(await parseError(res, 'Invalid credentials'))
  return res.json()
}

export async function sendChatStream(token, message, sessionId, onToken) {
  const res = await fetch(`${BASE}/chat/stream`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!res.ok) throw new Error((await res.json()).detail)

  const newSessionId = res.headers.get('X-Session-Id') || sessionId
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop()
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const token = line.slice(6)
        if (token !== '[DONE]') onToken(token)
      }
    }
  }
  return newSessionId
}

export async function getSteps(token) {
  const res = await fetch(`${BASE}/certify/steps`, { headers: authHeaders(token) })
  if (!res.ok) throw new Error('Failed to load steps')
  return res.json() // { steps }
}

export async function autofill(token, chatHistory) {
  const res = await fetch(`${BASE}/certify/autofill`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ chat_history: chatHistory }),
  })
  if (!res.ok) throw new Error('Autofill failed')
  return res.json() // { fields }
}

export async function generateCert(token, formData) {
  const res = await fetch(`${BASE}/certify/generate`, {
    method: 'POST',
    headers: authHeaders(token),
    body: JSON.stringify({ form_data: formData }),
  })
  if (!res.ok) throw new Error('Certificate generation failed')
  return res.blob()
}
