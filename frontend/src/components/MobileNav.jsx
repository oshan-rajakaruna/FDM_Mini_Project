import { AnimatePresence, motion } from 'framer-motion'
import { Menu, X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { NavLink } from 'react-router-dom'
import BrandMark from './BrandMark'
import { navigationItems } from './navigation'

export default function MobileNav({ open, onOpen, onClose }) {
  const closeButtonRef = useRef(null)
  const drawerRef = useRef(null)
  const triggerButtonRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeButtonRef.current?.focus()

    const handleDialogKeys = (event) => {
      if (event.key === 'Escape') {
        onClose()
        return
      }
      if (event.key !== 'Tab') return

      const focusableElements = drawerRef.current?.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), [tabindex]:not([tabindex="-1"])',
      )
      if (!focusableElements?.length) return

      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]
      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault()
        lastElement.focus()
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault()
        firstElement.focus()
      }
    }
    document.addEventListener('keydown', handleDialogKeys)

    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', handleDialogKeys)
      triggerButtonRef.current?.focus()
    }
  }, [open, onClose])

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-40 flex h-[4.75rem] items-center justify-between border-b border-white/10 bg-[#071425]/85 px-5 backdrop-blur-2xl md:hidden">
        <BrandMark />
        <button
          ref={triggerButtonRef}
          type="button"
          onClick={onOpen}
          className="grid size-11 place-items-center rounded-xl border border-white/10 bg-white/[0.06] text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
          aria-label="Open navigation menu"
          aria-expanded={open}
        >
          <Menu aria-hidden="true" size={22} />
        </button>
      </header>

      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-50 md:hidden">
            <motion.button
              type="button"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={onClose}
              className="absolute inset-0 bg-slate-950/75 backdrop-blur-sm"
              aria-label="Close navigation menu"
            />
            <motion.aside
              ref={drawerRef}
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 300, damping: 32 }}
              className="absolute inset-y-0 left-0 w-[min(86vw,21rem)] border-r border-white/10 bg-[#081629] p-5 shadow-2xl"
              role="dialog"
              aria-modal="true"
              aria-label="Mobile navigation"
            >
              <div className="flex items-center justify-between">
                <BrandMark />
                <button
                  ref={closeButtonRef}
                  type="button"
                  onClick={onClose}
                  className="grid size-10 place-items-center rounded-xl text-slate-300 hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-cyan-300"
                  aria-label="Close navigation menu"
                >
                  <X aria-hidden="true" size={21} />
                </button>
              </div>
              <nav className="mt-10 space-y-2">
                {navigationItems.map(({ label, to, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `flex min-h-13 items-center gap-3 rounded-xl border px-4 py-3.5 text-sm font-bold transition ${
                        isActive
                          ? 'border-cyan-300/20 bg-cyan-300/10 text-white'
                          : 'border-transparent text-slate-400 hover:bg-white/[0.06] hover:text-white'
                      }`
                    }
                  >
                    <Icon aria-hidden="true" size={21} strokeWidth={1.8} />
                    {label}
                  </NavLink>
                ))}
              </nav>
              <div className="absolute inset-x-5 bottom-6 rounded-2xl border border-white/10 bg-white/[0.045] p-4 text-xs leading-5 text-slate-400">
                RainWise decision support<br />
                Local prediction API configured.
              </div>
            </motion.aside>
          </div>
        )}
      </AnimatePresence>
    </>
  )
}
