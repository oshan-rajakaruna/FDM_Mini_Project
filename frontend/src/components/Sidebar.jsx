import { ChevronsLeft, ChevronsRight } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import BrandMark from './BrandMark'
import { navigationItems } from './navigation'

export default function Sidebar({ collapsed, onToggle }) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 hidden border-r border-white/10 bg-[#071425]/90 px-4 py-5 backdrop-blur-2xl transition-[width] duration-300 md:flex md:flex-col ${
        collapsed ? 'w-[5.5rem]' : 'w-[17.5rem]'
      }`}
      aria-label="Primary navigation"
    >
      <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'}`}>
        <BrandMark compact={collapsed} />
        {!collapsed && (
          <button
            type="button"
            onClick={onToggle}
            className="grid size-9 place-items-center rounded-xl text-slate-400 transition hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
            aria-label="Collapse sidebar"
          >
            <ChevronsLeft aria-hidden="true" size={19} />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          type="button"
          onClick={onToggle}
          className="mx-auto mt-5 grid size-9 place-items-center rounded-xl text-slate-400 transition hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
          aria-label="Expand sidebar"
        >
          <ChevronsRight aria-hidden="true" size={19} />
        </button>
      )}

      <nav className="mt-10 flex flex-1 flex-col gap-2">
        {navigationItems.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            title={collapsed ? label : undefined}
            className={({ isActive }) =>
              `group relative flex min-h-12 items-center rounded-xl border text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300 ${
                collapsed ? 'justify-center px-0' : 'gap-3 px-3.5'
              } ${
                isActive
                  ? 'border-cyan-300/20 bg-cyan-300/10 text-white shadow-[inset_3px_0_0_#54d8f0]'
                  : 'border-transparent text-slate-400 hover:border-white/5 hover:bg-white/[0.055] hover:text-slate-100'
              }`
            }
          >
            <Icon aria-hidden="true" className="shrink-0" size={20} strokeWidth={1.8} />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {!collapsed && (
        <div className="rounded-2xl border border-sky-300/10 bg-sky-300/[0.055] p-4">
          <p className="text-[0.67rem] font-bold uppercase tracking-[0.17em] text-sky-200/70">
            Service connection
          </p>
          <div className="mt-2 flex items-center gap-2 text-sm font-semibold text-slate-200">
            <span className="size-2 rounded-full border border-cyan-200/60 bg-cyan-300/35" aria-hidden="true" />
            Checked on request
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-400">
            Start the RainWise backend before predicting or opening history.
          </p>
        </div>
      )}
    </aside>
  )
}

