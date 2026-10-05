import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import { useEffect } from 'react'
import AppShell from './components/AppShell'
import HomePage from './pages/HomePage'
import PredictPage from './pages/PredictPage'
import HistoryPage from './pages/HistoryPage'
import AboutPage from './pages/AboutPage'
import HelpPage from './pages/HelpPage'

function ScrollToTop() {
  const { pathname } = useLocation()

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [pathname])

  return null
}

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <ScrollToTop />
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="predict" element={<PredictPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="help" element={<HelpPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </MotionConfig>
  )
}
