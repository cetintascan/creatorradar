import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import { get } from '../api'

const COLORS = {
  positive: '#10B981',
  negative: '#EF4444',
  neutral: '#6366F1',
}

function DemandChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 4, right: 16, bottom: 60, left: 0 }}>
        <XAxis
          dataKey="topic"
          tick={{ fontSize: 11, fill: '#6B7280' }}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis tick={{ fontSize: 11, fill: '#6B7280' }} />
        <Tooltip
          formatter={(v) => [v?.toFixed(3), 'Demand Score']}
          contentStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="demand_score" radius={[4, 4, 0, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS.neutral} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

function TrendingChart({ data }) {
  const hasDeltas = data.some((d) => d.demand_delta_pct != null)
  if (!hasDeltas) {
    return (
      <div className="flex items-center justify-center h-40 text-sm text-gray-400">
        Not enough historical data — trending requires 14 days.
      </div>
    )
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 4, right: 16, bottom: 60, left: 0 }}>
        <XAxis
          dataKey="topic"
          tick={{ fontSize: 11, fill: '#6B7280' }}
          angle={-35}
          textAnchor="end"
          interval={0}
        />
        <YAxis
          tickFormatter={(v) => `${v}%`}
          tick={{ fontSize: 11, fill: '#6B7280' }}
        />
        <Tooltip
          formatter={(v) => [v != null ? `${v.toFixed(1)}%` : '—', '7-day Δ']}
          contentStyle={{ fontSize: 12 }}
        />
        <Bar dataKey="demand_delta_pct" radius={[4, 4, 0, 0]}>
          {data.map((d, i) => (
            <Cell
              key={i}
              fill={
                d.demand_delta_pct == null
                  ? '#D1D5DB'
                  : d.demand_delta_pct >= 0
                  ? COLORS.positive
                  : COLORS.negative
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function CategoryTrends() {
  const [demand, setDemand] = useState([])
  const [trending, setTrending] = useState([])
  const [tab, setTab] = useState('demand')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([get('/api/categories'), get('/api/categories/trending')])
      .then(([d, t]) => {
        setDemand(d)
        setTrending(t)
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-800 mb-4">Category Intelligence</h1>

      <div className="flex gap-2 mb-6">
        {['demand', 'trending'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              tab === t
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-300'
            }`}
          >
            {t === 'demand' ? 'Demand Today' : '7-Day Trend'}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-xl shadow p-6">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-sm text-gray-400">
            Loading…
          </div>
        ) : tab === 'demand' ? (
          <DemandChart data={demand} />
        ) : (
          <TrendingChart data={trending} />
        )}
      </div>

      <div className="mt-6 bg-white rounded-xl shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {['Category', 'Videos', 'Total Views', 'Sponsor Density', 'Commerce Density', 'Demand Score'].map((h) => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {demand.map((d) => (
              <tr key={d.topic} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-800 text-sm">{d.topic}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{d.video_count?.toLocaleString('tr-TR')}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{d.total_views?.toLocaleString('tr-TR')}</td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {d.sponsor_density != null ? `${(d.sponsor_density * 100).toFixed(1)}%` : '—'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {d.commerce_intent_density != null ? `${(d.commerce_intent_density * 100).toFixed(1)}%` : '—'}
                </td>
                <td className="px-4 py-3 text-sm font-semibold text-indigo-600">
                  {d.demand_score?.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
