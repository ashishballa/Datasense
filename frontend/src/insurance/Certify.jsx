import { useState, useEffect } from 'react'
import { getSteps, autofill, generateCert } from './api'

export default function Certify({ token, chatHistory }) {
  const [steps, setSteps] = useState([])
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState({})
  const [filling, setFilling] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [done, setDone] = useState(false)

  useEffect(() => {
    getSteps(token).then(d => setSteps(d.steps)).catch(() => {})
  }, [token])

  function setValue(key, value) {
    setFormData(prev => ({ ...prev, [key]: value }))
  }

  async function handleAutofill() {
    if (!chatHistory.length) return
    setFilling(true)
    try {
      const data = await autofill(token, chatHistory)
      setFormData(prev => ({ ...prev, ...data.fields }))
    } catch (err) {
      alert('Autofill failed: ' + err.message)
    } finally {
      setFilling(false)
    }
  }

  async function handleGenerate() {
    setGenerating(true)
    try {
      const blob = await generateCert(token, formData)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'insurance_certificate.pdf'
      a.click()
      URL.revokeObjectURL(url)
      setDone(true)
    } catch (err) {
      alert('Failed to generate certificate: ' + err.message)
    } finally {
      setGenerating(false)
    }
  }

  if (!steps.length) return <div className="ins-certify-loading">Loading form…</div>

  const step = steps[currentStep]
  const isLast = currentStep === steps.length - 1

  return (
    <div className="ins-certify">
      <div className="ins-certify-header">
        <h3>Insurance Certificate</h3>
        <button
          className="ins-autofill-btn"
          onClick={handleAutofill}
          disabled={filling || !chatHistory.length}
          title={!chatHistory.length ? 'Chat first to enable autofill' : ''}
        >
          {filling ? 'Filling…' : 'Autofill from Chat'}
        </button>
      </div>

      {/* Step progress */}
      <div className="ins-steps">
        {steps.map((s, i) => (
          <button
            key={s.id}
            className={`ins-step-pill ${i === currentStep ? 'active' : ''} ${i < currentStep ? 'done' : ''}`}
            onClick={() => setCurrentStep(i)}
          >
            {i + 1}. {s.title}
          </button>
        ))}
      </div>

      {/* Current step fields */}
      <div className="ins-form-step">
        <h4>{step.title}</h4>
        {step.fields.map(field => (
          <div key={field.key} className="ins-field">
            <label>{field.label}</label>
            {field.type === 'select' ? (
              <select
                value={formData[field.key] ?? ''}
                onChange={e => setValue(field.key, e.target.value)}
              >
                <option value="">Select…</option>
                {field.options.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            ) : field.type === 'boolean' ? (
              <div className="ins-bool">
                {['Yes', 'No'].map(v => (
                  <label key={v} className="ins-radio">
                    <input
                      type="radio"
                      name={field.key}
                      value={v}
                      checked={formData[field.key] === (v === 'Yes')}
                      onChange={() => setValue(field.key, v === 'Yes')}
                    />
                    {v}
                  </label>
                ))}
              </div>
            ) : (
              <input
                type={field.type === 'number' ? 'number' : field.type}
                value={formData[field.key] ?? ''}
                onChange={e => setValue(field.key, field.type === 'number' ? Number(e.target.value) : e.target.value)}
                placeholder={field.label}
              />
            )}
          </div>
        ))}
      </div>

      {/* Navigation */}
      <div className="ins-certify-nav">
        <button onClick={() => setCurrentStep(s => s - 1)} disabled={currentStep === 0} className="ins-btn-secondary">
          Back
        </button>
        {isLast ? (
          <button onClick={handleGenerate} disabled={generating} className="ins-btn-primary">
            {generating ? 'Generating…' : done ? 'Download Again' : 'Generate Certificate'}
          </button>
        ) : (
          <button onClick={() => setCurrentStep(s => s + 1)} className="ins-btn-primary">
            Next
          </button>
        )}
      </div>

      {done && <p className="ins-success">Certificate downloaded!</p>}
    </div>
  )
}
