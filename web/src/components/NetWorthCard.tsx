import type { NetWorth } from '../api'
import { AddAssetsDropdown } from './AddAssetsDropdown'

interface Props {
  data: NetWorth | null
  householdName: string
  onOpenCasImport: () => void
}

function formatInr(value: string): string {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
  }).format(Number(value))
}

export function NetWorthCard({ data, householdName, onOpenCasImport }: Props) {
  const hasData = data !== null && data.as_of !== null

  return (
    <>
      <header className="app-header">
        <h1>corpus-watch</h1>
        <span className="household-name">{householdName}</span>
      </header>

      <div className="networth-card">
        <h2>Net worth</h2>
        <div className="networth-amount">
          {hasData ? formatInr(data!.total) : '₹ —'}
        </div>
        {hasData ? (
          <p className="networth-meta">
            Mutual funds · as of {data!.as_of}
          </p>
        ) : (
          <p className="networth-meta">No assets yet.</p>
        )}
        <AddAssetsDropdown onSelectCas={onOpenCasImport} />
      </div>
    </>
  )
}
