import { useEffect, useState } from 'react'
import { getNetworth, getNetworthHistory, getSetup } from './api'
import type { NetWorth, NetWorthHistory, SetupStatus } from './api'
import { AppHeader } from './components/AppHeader'
import { CasImportModal } from './components/CasImportModal'
import { NetWorthCard } from './components/NetWorthCard'
import { NetWorthChart } from './components/NetWorthChart'
import { SetupScreen } from './components/SetupScreen'
import './index.css'

export default function App() {
  const [setup, setSetup] = useState<SetupStatus | null>(null)
  const [networth, setNetworth] = useState<NetWorth | null>(null)
  const [history, setHistory] = useState<NetWorthHistory | null>(null)
  const [showCasModal, setShowCasModal] = useState(false)

  useEffect(() => {
    getSetup().then(setSetup).catch(console.error)
  }, [])

  useEffect(() => {
    if (setup?.configured) {
      getNetworth().then(setNetworth).catch(console.error)
      getNetworthHistory().then(setHistory).catch(console.error)
    }
  }, [setup])

  useEffect(() => {
    if (!networth?.refreshing) return
    const id = setInterval(() => {
      getNetworth().then(setNetworth).catch(console.error)
      getNetworthHistory().then(setHistory).catch(console.error)
    }, 5000)
    return () => clearInterval(id)
  }, [networth?.refreshing])

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
    <>
      <AppHeader
        householdName={setup.household_name ?? ''}
        individuals={setup.individuals ?? []}
      />
      <main className="app">
        <NetWorthCard
          data={networth}
          onOpenCasImport={() => setShowCasModal(true)}
        />
        {history && (
          <div className="graph-card">
            <NetWorthChart history={history} refreshing={networth?.refreshing} />
          </div>
        )}
        {showCasModal && (
          <CasImportModal
            onClose={() => setShowCasModal(false)}
            onImported={() => {
              setShowCasModal(false)
              getNetworth().then(setNetworth).catch(console.error)
              getNetworthHistory().then(setHistory).catch(console.error)
            }}
          />
        )}
      </main>
    </>
  )
}
