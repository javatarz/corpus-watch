import { useEffect, useState } from 'react'
import { getNetworth, getSetup } from './api'
import type { NetWorth, SetupStatus } from './api'
import { CasImportModal } from './components/CasImportModal'
import { NetWorthCard } from './components/NetWorthCard'
import { SetupScreen } from './components/SetupScreen'
import './index.css'

export default function App() {
  const [setup, setSetup] = useState<SetupStatus | null>(null)
  const [networth, setNetworth] = useState<NetWorth | null>(null)
  const [showCasModal, setShowCasModal] = useState(false)

  useEffect(() => {
    getSetup().then(setSetup).catch(console.error)
  }, [])

  useEffect(() => {
    if (setup?.configured) {
      getNetworth().then(setNetworth).catch(console.error)
    }
  }, [setup])

  if (setup === null) {
    return <div className="loading">Loading…</div>
  }

  if (!setup.configured) {
    return (
      <SetupScreen
        onComplete={() => {
          getSetup().then(setSetup).catch(console.error)
        }}
      />
    )
  }

  return (
    <main className="app">
      <NetWorthCard
        data={networth}
        householdName={setup.household_name ?? ''}
        onOpenCasImport={() => setShowCasModal(true)}
      />
      {showCasModal && (
        <CasImportModal
          onClose={() => setShowCasModal(false)}
          onImported={() => {
            setShowCasModal(false)
            getNetworth().then(setNetworth).catch(console.error)
          }}
        />
      )}
    </main>
  )
}
