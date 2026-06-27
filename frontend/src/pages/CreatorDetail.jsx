import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { get } from '../api'

const fmt = (n) => n?.toLocaleString('tr-TR') ?? '—'
const pct = (n) => (n != null ? `${(n * 100).toFixed(1)}%` : '—')
const score = (n) => (n != null ? `${(n * 100).toFixed(0)}%` : '—')
const dateStr = (s) => (s ? new Date(s).toLocaleDateString('tr-TR') : '—')

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl shadow px-5 py-4">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

function Badge({ active, label }) {
  return active ? (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700">
      {label}
    </span>
  ) : null
}

export default function CreatorDetail() {
  const { channelId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    get(`/api/creators/${channelId}`)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [channelId])

  if (loading) {
    return <div className="text-sm text-gray-400 py-10 text-center">Loading…</div>
  }
  if (error) {
    return (
      <div className="bg-red-50 text-red-700 text-sm rounded-md px-4 py-3">{error}</div>
    )
  }

  const { profile: p, videos } = data

  return (
    <div>
      <button
        onClick={() => navigate('/')}
        className="text-sm text-indigo-600 hover:underline mb-4 inline-flex items-center gap-1"
      >
        ← Back to Leaderboard
      </button>

      <div className="flex items-baseline gap-3 mb-5">
        <h1 className="text-2xl font-bold text-gray-900">{p.channel_title}</h1>
        <span className="text-gray-400 text-sm">{p.handle}</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 mb-6">
        <StatCard label="Fit Score" value={score(p.commercial_fit_score)} />
        <StatCard label="Subscribers" value={fmt(p.subscriber_count)} />
        <StatCard label="Sponsor Rate" value={pct(p.sponsor_signal_rate)} />
        <StatCard label="Commerce Rate" value={pct(p.commerce_intent_rate)} />
        <StatCard label="Avg Engagement" value={pct(p.avg_engagement_rate)} />
      </div>

      <h2 className="text-base font-semibold text-gray-700 mb-3">Recent Videos</h2>
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {['Title', 'Published', 'Views', 'Engagement', 'Signals'].map((h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {videos.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400 text-sm">
                  No video signals available.
                </td>
              </tr>
            ) : (
              videos.map((v) => (
                <tr key={v.video_id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-800 max-w-xs truncate">
                    {v.video_title}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                    {dateStr(v.published_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{fmt(v.view_count)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{pct(v.engagement_rate)}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1.5 flex-wrap">
                      <Badge active={v.has_sponsor_signal} label="Sponsor" />
                      <Badge active={v.has_commerce_intent} label="Commerce" />
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
