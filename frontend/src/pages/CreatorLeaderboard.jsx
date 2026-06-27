import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { get } from '../api'

function ScoreBar({ value }) {
  const pct = Math.round((value ?? 0) * 100)
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 bg-gray-200 rounded-full h-1.5">
        <div
          className="bg-indigo-500 h-1.5 rounded-full"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 w-8">{pct}%</span>
    </div>
  )
}

function SignalDot({ active }) {
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${
        active ? 'bg-emerald-500' : 'bg-gray-300'
      }`}
    />
  )
}

const fmt = (n) => n?.toLocaleString('tr-TR') ?? '—'
const pct = (n) => (n != null ? `${(n * 100).toFixed(1)}%` : '—')

export default function CreatorLeaderboard() {
  const navigate = useNavigate()
  const [creators, setCreators] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    get('/api/categories')
      .then((data) => setCategories(data.map((c) => c.topic)))
      .catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    const url = selectedCategory
      ? `/api/creators?category=${encodeURIComponent(selectedCategory)}`
      : '/api/creators'
    get(url)
      .then(setCreators)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [selectedCategory])

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-gray-800">Creator Leaderboard</h1>
        <select
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
        >
          <option value="">All Categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 text-sm rounded-md px-4 py-3 mb-4">{error}</div>
      )}

      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {['#', 'Creator', 'Subscribers', 'Fit Score', 'Sponsor', 'Commerce'].map((h) => (
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
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">
                  Loading…
                </td>
              </tr>
            ) : creators.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">
                  No creators found.
                </td>
              </tr>
            ) : (
              creators.map((c, i) => (
                <tr
                  key={c.channel_id}
                  className="hover:bg-indigo-50 cursor-pointer transition-colors"
                  onClick={() => navigate(`/creators/${c.channel_id}`)}
                >
                  <td className="px-4 py-3 text-sm text-gray-400">{i + 1}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{c.channel_title}</div>
                    <div className="text-xs text-gray-400">{c.handle}</div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{fmt(c.subscriber_count)}</td>
                  <td className="px-4 py-3">
                    <ScoreBar value={c.commercial_fit_score} />
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-1.5">
                      <SignalDot active={c.sponsor_signal_rate > 0} />
                      <span className="text-gray-600">{pct(c.sponsor_signal_rate)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <div className="flex items-center gap-1.5">
                      <SignalDot active={c.commerce_intent_rate > 0} />
                      <span className="text-gray-600">{pct(c.commerce_intent_rate)}</span>
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
