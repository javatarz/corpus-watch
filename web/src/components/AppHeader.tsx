interface Props {
  householdName: string
  individuals: string[]
}

function LogoMark() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="var(--accent)" />
      <rect x="6" y="20" width="4" height="7" rx="1" fill="white" opacity="0.75" />
      <rect x="14" y="14" width="4" height="13" rx="1" fill="white" opacity="0.9" />
      <rect x="22" y="8" width="4" height="19" rx="1" fill="white" />
    </svg>
  )
}

export function AppHeader({ householdName, individuals }: Props) {
  return (
    <nav className="topbar" aria-label="Site header">
      <div className="topbar-brand">
        <LogoMark />
        <span className="topbar-appname">Corpus Watch</span>
      </div>
      <div className="topbar-identity">
        <span className="topbar-household">{householdName}</span>
        {individuals.length > 0 && (
          <span className="topbar-individuals">
            {individuals.join(' · ')}
          </span>
        )}
      </div>
    </nav>
  )
}
