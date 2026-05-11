import { useState } from 'react'
import { postSetup } from '../api'

interface Props {
  onComplete: () => void
}

export function SetupScreen({ onComplete }: Props) {
  const [name, setName] = useState('')
  const [householdName, setHouseholdName] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function handleNameChange(value: string) {
    setName(value)
    const parts = value.trim().split(/\s+/)
    if (parts.length >= 2) {
      setHouseholdName(`${parts[parts.length - 1]} Family`)
    } else {
      setHouseholdName('')
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    try {
      await postSetup({ individual_name: name, household_name: householdName })
      onComplete()
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="setup-screen">
      <h1>corpus-watch</h1>
      <p>Welcome. Set up your household to begin.</p>
      <form onSubmit={handleSubmit}>
        <label>
          Your name
          <input
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label>
          Household name
          <input
            value={householdName}
            onChange={(e) => setHouseholdName(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={submitting}>
          Get started
        </button>
      </form>
    </div>
  )
}
