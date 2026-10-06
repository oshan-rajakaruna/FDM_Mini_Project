import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import MobileNav from './MobileNav'
import Sidebar from './Sidebar'
import WeatherBackground from './WeatherBackground'

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen overflow-x-hidden bg-midnight text-slate-100">
      <WeatherBackground />
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
      <MobileNav
        open={mobileOpen}
        onOpen={() => setMobileOpen(true)}
        onClose={() => setMobileOpen(false)}
      />
      <div
        className={`relative z-10 min-h-screen pt-[4.75rem] transition-[padding] duration-300 md:pt-0 ${
          collapsed ? 'md:pl-[5.5rem]' : 'md:pl-[17.5rem]'
        }`}
      >
        <main>
          <Outlet />
        </main>
        <footer className="mx-auto flex w-full max-w-[1440px] flex-col gap-2 border-t border-white/10 px-5 py-7 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-7 lg:px-10">
          <span>RainWise · Weather-risk decision support</span>
          <span>Local prediction API configured</span>
        </footer>
      </div>
    </div>
  )
}

