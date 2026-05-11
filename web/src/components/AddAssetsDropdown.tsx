import { useEffect, useRef, useState } from 'react'

interface Props {
  onSelectCas: () => void
}

export function AddAssetsDropdown({ onSelectCas }: Props) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  function handleSelectMf() {
    setOpen(false)
    onSelectCas()
  }

  return (
    <div className="dropdown" ref={ref}>
      <button
        type="button"
        className="dropdown-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        + Add assets ▾
      </button>
      {open && (
        <ul className="dropdown-menu" role="listbox">
          <li role="option">
            <button type="button" onClick={handleSelectMf}>
              Mutual Funds
            </button>
          </li>
          <li className="disabled" role="option" aria-disabled="true">
            Stocks <span className="badge">coming soon</span>
          </li>
          <li className="disabled" role="option" aria-disabled="true">
            Fixed Deposits <span className="badge">coming soon</span>
          </li>
          <li className="disabled" role="option" aria-disabled="true">
            EPF <span className="badge">coming soon</span>
          </li>
        </ul>
      )}
    </div>
  )
}
