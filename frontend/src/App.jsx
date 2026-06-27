import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import CreatorLeaderboard from './pages/CreatorLeaderboard'
import CategoryTrends from './pages/CategoryTrends'
import CreatorDetail from './pages/CreatorDetail'

function Nav() {
  const link = ({ isActive }) =>
    `px-4 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive ? 'bg-indigo-700 text-white' : 'text-indigo-100 hover:bg-indigo-700'
    }`

  return (
    <nav className="bg-indigo-600 shadow">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
        <span className="text-white font-bold text-lg tracking-tight">CreatorRadar</span>
        <NavLink to="/" className={link} end>Creators</NavLink>
        <NavLink to="/categories" className={link}>Categories</NavLink>
      </div>
    </nav>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<CreatorLeaderboard />} />
          <Route path="/categories" element={<CategoryTrends />} />
          <Route path="/creators/:channelId" element={<CreatorDetail />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
