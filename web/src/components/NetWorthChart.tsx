import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { NetWorthHistory } from '../api'

interface Props {
  history: NetWorthHistory
  refreshing?: boolean
}

const CLASS_COLORS: Record<string, string> = {
  MF: '#aa3bff',
  Stocks: '#2563eb',
}

const FALLBACK_COLORS = ['#16a34a', '#ea580c', '#0891b2', '#db2777']

function colorFor(cls: string, index: number): string {
  return CLASS_COLORS[cls] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]
}

function formatInr(value: number): string {
  const lakhs = value / 100000
  return `₹${lakhs.toFixed(2)}L`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: '2-digit' })
}

function CustomTooltip({ active, payload, label }: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}) {
  if (!active || !payload?.length) return null

  const total = payload.reduce((sum, p) => sum + p.value, 0)

  return (
    <div style={{
      background: '#fff',
      border: '1px solid #e5e4e7',
      borderRadius: 8,
      padding: '10px 14px',
      boxShadow: 'rgba(0,0,0,0.1) 0 4px 16px',
      fontSize: 13,
      color: '#6b6375',
      lineHeight: 1.6,
    }}>
      <div style={{ fontWeight: 600, color: '#08060d', marginBottom: 4 }}>
        {label ? formatDate(label) : ''}
      </div>
      <div style={{ color: '#08060d', fontWeight: 600 }}>Total: {formatInr(total)}</div>
      {payload.map(p => (
        <div key={p.name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: p.color, display: 'inline-block' }} />
          {p.name}: {formatInr(p.value)}
        </div>
      ))}
    </div>
  )
}

export function NetWorthChart({ history, refreshing }: Props) {
  const { series, asset_classes } = history

  if (!series.length) {
    return (
      <div style={{ fontSize: 14, padding: '24px 0', textAlign: 'center', color: '#9ca3af' }}>
        {refreshing
          ? 'Fetching historical prices in the background — the graph will appear shortly.'
          : 'No historical data yet. Import a CAS statement to get started.'}
      </div>
    )
  }

  const chartData = series.map(point => {
    const row: Record<string, string | number> = { date: point.date }
    for (const cls of asset_classes) {
      row[cls] = point[cls] ? Number(point[cls]) : 0
    }
    return row
  })

  const maxTotal = Math.max(...series.map(p => Number(p.total)))
  const yMax = Math.ceil((maxTotal / 100000) * 1.1) * 100000

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <p style={{ fontSize: 14, fontWeight: 600, color: '#08060d', margin: 0 }}>Net worth over time</p>
        <div style={{ display: 'flex', gap: 16 }}>
          {asset_classes.map((cls, i) => (
            <div key={cls} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#6b6375' }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: colorFor(cls, i), display: 'inline-block' }} />
              {cls === 'MF' ? 'Mutual funds' : cls}
            </div>
          ))}
        </div>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={chartData} margin={{ top: 10, right: 16, bottom: 0, left: 44 }}>
          <defs>
            {asset_classes.map((cls, i) => {
              const color = colorFor(cls, i)
              return (
                <linearGradient key={cls} id={`grad-${cls}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                  <stop offset="100%" stopColor={color} stopOpacity={0.08} />
                </linearGradient>
              )
            })}
          </defs>
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            tick={{ fontSize: 11, fill: '#6b6375' }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            domain={[0, yMax]}
            tickFormatter={v => `₹${(v / 100000).toFixed(0)}L`}
            tick={{ fontSize: 11, fill: '#6b6375' }}
            tickLine={false}
            axisLine={false}
            width={44}
          />
          <Tooltip content={<CustomTooltip />} />
          {asset_classes.map((cls, i) => {
            const color = colorFor(cls, i)
            return (
              <Area
                key={cls}
                type="monotone"
                dataKey={cls}
                name={cls === 'MF' ? 'Mutual funds' : cls}
                stackId="1"
                stroke={color}
                strokeWidth={1.5}
                fill={`url(#grad-${cls})`}
              />
            )
          })}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
