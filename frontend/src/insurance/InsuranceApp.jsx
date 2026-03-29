import { useState } from 'react'
import Login from './Login'
import Chat from './Chat'
import Certify from './Certify'

export default function InsuranceApp() {
  const [token, setToken] = useState(null)
  const [username, setUsername] = useState(null)
  const [chatHistory, setChatHistory] = useState([])

  function handleLogin(tok, user) {
    setToken(tok)
    setUsername(user)
  }

  function handleLogout() {
    setToken(null)
    setUsername(null)
    setChatHistory([])
  }

  if (!token) return <Login onLogin={handleLogin} />

  return (
    <div className="ins-app">
      <div className="ins-topbar">
        <span className="ins-topbar-title">Home Insurance Assistant</span>
        <span className="ins-topbar-user">
          {username}
          <button onClick={handleLogout} className="ins-logout">Sign out</button>
        </span>
      </div>
      <div className="ins-layout">
        <Chat token={token} onHistoryChange={setChatHistory} />
        <Certify token={token} chatHistory={chatHistory} />
      </div>
    </div>
  )
}
