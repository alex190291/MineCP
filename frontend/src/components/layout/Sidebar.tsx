import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, PlusCircle, Users, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { cn } from '@/utils/cn';
import { GlassCard } from '@/components/common/GlassCard';

const navItems = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/servers/new', labelKey: 'nav.createServer', icon: PlusCircle },
  { to: '/users', labelKey: 'nav.users', icon: Users },
  { to: '/settings', labelKey: 'nav.settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { t } = useTranslation();

  return (
    <aside className="p-4 h-screen w-64 flex-shrink-0">
      <GlassCard className="h-full p-4 flex flex-col gap-4 sticky top-4">
        <div className="flex items-center gap-3 px-3 py-2">
          <img
            src="/logo.png"
            alt="MineCP Logo"
            className="h-12 w-auto"
          />
          <span className="text-2xl font-bold">MineCP</span>
        </div>

        <div className="border-t border-white/10" />

        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const label = t(item.labelKey);
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition-all',
                    isActive
                      ? 'bg-white/15 text-white'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  )
                }
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                <span>{label}</span>
              </NavLink>
            );
          })}
        </nav>
      </GlassCard>
    </aside>
  );
};
