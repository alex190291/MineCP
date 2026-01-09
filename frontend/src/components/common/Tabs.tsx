import React, { useState } from 'react';
import { cn } from '@/utils/cn';

interface Tab {
  id: string;
  label: string;
  icon?: React.ReactNode;
}

interface TabsProps {
  tabs: Tab[];
  defaultTab?: string;
  children: (activeTab: string) => React.ReactNode;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, defaultTab, children }) => {
  const [activeTab, setActiveTab] = useState(defaultTab || tabs[0]?.id);

  return (
    <div>
      {/* Tab Headers */}
      <div className="flex gap-2 mb-6 overflow-x-auto custom-scrollbar pb-2">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'btn secondary flex items-center gap-2 whitespace-nowrap',
              activeTab === tab.id && 'opacity-100 shadow-[0_4px_8px_rgba(255,255,255,0.15)] -translate-y-0.5'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>{children(activeTab)}</div>
    </div>
  );
};
