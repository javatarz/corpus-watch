import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { CasImportModal } from './CasImportModal'
import * as api from '../api'

vi.mock('../api', () => ({
  importCas: vi.fn(),
}))

describe('CasImportModal', () => {
  const onClose = vi.fn()
  const onImported = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders form with file picker and password field', () => {
    render(<CasImportModal onClose={onClose} onImported={onImported} />)
    expect(screen.getByText('Choose file')).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /import/i })).toBeDisabled()
  })

  it('enables Import button once file is chosen', async () => {
    const user = userEvent.setup()
    render(<CasImportModal onClose={onClose} onImported={onImported} />)

    const file = new File(['%PDF-1.4'], 'statement.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')!
    await user.upload(input, file)

    expect(screen.getByRole('button', { name: /import/i })).not.toBeDisabled()
    expect(screen.getByText('statement.pdf')).toBeInTheDocument()
  })

  it('calls onImported on successful submit', async () => {
    const user = userEvent.setup()
    vi.mocked(api.importCas).mockResolvedValue({
      imported: 1,
      skipped: 0,
      total: '12345.60',
      currency: 'INR',
      as_of: '2024-12-31',
    })

    render(<CasImportModal onClose={onClose} onImported={onImported} />)

    const file = new File(['%PDF-1.4'], 'statement.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')!
    await user.upload(input, file)
    await user.type(screen.getByLabelText(/password/i), 'MYPAN')
    await user.click(screen.getByRole('button', { name: /import/i }))

    await waitFor(() => expect(onImported).toHaveBeenCalledOnce())
  })

  it('shows error on incorrect password', async () => {
    const user = userEvent.setup()
    vi.mocked(api.importCas).mockRejectedValue(new Error('Incorrect password'))

    render(<CasImportModal onClose={onClose} onImported={onImported} />)

    const file = new File(['%PDF-1.4'], 'statement.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')!
    await user.upload(input, file)
    await user.click(screen.getByRole('button', { name: /import/i }))

    await waitFor(() =>
      expect(screen.getByText(/incorrect password/i)).toBeInTheDocument(),
    )
    expect(onImported).not.toHaveBeenCalled()
  })

  it('shows discard confirm when closing with file selected', async () => {
    const user = userEvent.setup()
    render(<CasImportModal onClose={onClose} onImported={onImported} />)

    const file = new File(['%PDF-1.4'], 'statement.pdf', { type: 'application/pdf' })
    const input = document.querySelector<HTMLInputElement>('input[type="file"]')!
    await user.upload(input, file)
    await user.click(screen.getByLabelText('Close'))

    expect(screen.getByText('Discard import?')).toBeInTheDocument()
    expect(onClose).not.toHaveBeenCalled()
  })

  it('closes immediately when no data and X clicked', async () => {
    const user = userEvent.setup()
    render(<CasImportModal onClose={onClose} onImported={onImported} />)
    await user.click(screen.getByLabelText('Close'))
    expect(onClose).toHaveBeenCalledOnce()
  })
})
