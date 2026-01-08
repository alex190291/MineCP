import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, PlusCircle, Users, Settings, Menu } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { cn } from '@/utils/cn';
import { useUIStore } from '@/store/uiStore';
import { GlassCard } from '@/components/common/GlassCard';

const navItems = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/servers/new', labelKey: 'nav.createServer', icon: PlusCircle },
  { to: '/users', labelKey: 'nav.users', icon: Users },
  { to: '/settings', labelKey: 'nav.settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { t } = useTranslation();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        'p-4 h-screen transition-all duration-300 flex-shrink-0',
        sidebarOpen ? 'w-64' : 'w-20'
      )}
    >
      <GlassCard className="h-full p-4 flex flex-col gap-4 sticky top-4">
        <button
          onClick={toggleSidebar}
          className={cn(
            'flex items-center rounded-xl px-3 py-2 text-sm transition-all text-white/70 hover:bg-white/10 hover:text-white',
            sidebarOpen ? 'gap-3' : 'justify-center'
          )}
          title={sidebarOpen ? t('nav.collapseSidebar') : t('nav.expandSidebar')}
        >
          <Menu className="w-5 h-5 flex-shrink-0" />
          {sidebarOpen && <span>{t('nav.collapseSidebar')}</span>}
        </button>

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
                    'flex items-center rounded-xl px-3 py-2 text-sm transition-all',
                    sidebarOpen ? 'gap-3' : 'justify-center',
                    isActive
                      ? 'bg-white/15 text-white'
                      : 'text-white/70 hover:bg-white/10 hover:text-white'
                  )
                }
                title={!sidebarOpen ? label : undefined}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span>{label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </GlassCard>
    </aside>
  );
};
