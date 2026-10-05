import { CircleHelp, CloudRain, History, House, Info } from 'lucide-react'

export const navigationItems = [
  { label: 'Home', to: '/', icon: House },
  { label: 'Predict Rain', to: '/predict', icon: CloudRain },
  { label: 'History', to: '/history', icon: History },
  { label: 'About', to: '/about', icon: Info },
  { label: 'Help', to: '/help', icon: CircleHelp },
]

