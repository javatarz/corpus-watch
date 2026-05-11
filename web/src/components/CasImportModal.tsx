import { useRef, useState } from 'react'
import { importCas } from '../api'

type ModalState = 'idle' | 'loading' | 'confirm-discard'

interface Props {
  onClose: () => void
  onImported: () => void
}

export function CasImportModal({ onClose, onImported }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [state, setState] = useState<ModalState>('idle')
  const fileInputRef = useRef<HTMLInputElement>(null)

  function hasData() {
    return file !== null || password.length > 0
  }

  function handleClose() {
    if (hasData()) {
      setState('confirm-discard')
    } else {
      onClose()
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    setError(null)
    setState('loading')
    try {
      await importCas(file, password)
      onImported()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
      setState('idle')
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">
          <h2>Import Mutual Funds via CAS PDF</h2>
          <button
            type="button"
            className="modal-close"
            aria-label="Close"
            onClick={handleClose}
          >
            ✕
          </button>
        </div>

        {state === 'confirm-discard' ? (
          <div className="discard-confirm">
            <p>Discard import?</p>
            <p className="discard-sub">Your file selection will be lost.</p>
            <div className="discard-actions">
              <button type="button" onClick={() => setState('idle')}>
                Cancel
              </button>
              <button type="button" className="btn-danger" onClick={onClose}>
                Discard
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="field">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                id="cas-file"
                style={{ display: 'none' }}
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null)
                  setError(null)
                }}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
              >
                Choose file
              </button>
              <span className="file-name">
                {file ? file.name : 'No file chosen'}
              </span>
            </div>

            <label className="field">
              Password (optional)
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="off"
              />
              {error ? (
                <span className="field-error">⚠ {error}</span>
              ) : (
                <span className="field-hint">
                  Most CAS PDFs use your PAN as password.
                </span>
              )}
            </label>

            <div className="modal-footer">
              <button
                type="submit"
                disabled={!file || state === 'loading'}
              >
                {state === 'loading' ? 'Importing…' : 'Import'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
