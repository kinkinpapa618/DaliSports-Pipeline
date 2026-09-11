import React from 'react';
import { Trophy, Clock, Cpu, Share2, Settings } from 'lucide-react';
import { ActiveTab } from '../types';

interface BottomNavProps {
  currentTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  tournamentCount: number;
  isPipelineRunning: boolean;
}

export const BottomNav: React.FC<BottomNavProps> = ({
  currentTab,
  onTabChange,
  tournamentCount,
  isPipelineRunning,
}) => {
  const items = [
    {
      id: 'tournaments' as ActiveTab,
      label: 'Giải Đấu',
      icon: Trophy,
      badge: tournamentCount > 0 ? tournamentCount : undefined,
    },
    {
      id: 'timeline' as ActiveTab,
      label: 'Timeline',
      icon: Clock,
    },
    {
      id: 'pipeline' as ActiveTab,
      label: 'Pipeline',
      icon: Cpu,
      isLive: isPipelineRunning,
    },
    {
      id: 'seo' as ActiveTab,
      label: 'SEO',
      icon: Share2,
    },
    {
      id: 'settings' as ActiveTab,
      label: 'Cài Đặt',
      icon: Settings,
    },
  ];

  return (
    <nav className="md:hidden shrink-0 w-full z-30 bg-[var(--bg-sidebar)]/95 backdrop-blur-xl border-t border-[var(--border-subtle)] pb-[env(safe-area-inset-bottom,0px)] shadow-[0_-4px_20px_rgba(0,0,0,0.3)] transition-colors select-none">
      <div className="grid grid-cols-5 h-14 items-center px-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`flex flex-col items-center justify-center h-full relative cursor-pointer select-none transition-all duration-200 active:scale-95 ${
                isActive
                  ? 'text-[var(--accent-blue)] font-bold'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              <div className="relative flex items-center justify-center">
                <div
                  className={`w-8 h-6 rounded-full flex items-center justify-center transition-all ${
                    isActive
                      ? 'bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]'
                      : 'text-[var(--text-muted)]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'stroke-[2.5]' : 'stroke-2'}`} />
                </div>

                {item.badge !== undefined && (
                  <span className="absolute -top-1 -right-1.5 px-1.5 py-0.2 rounded-full text-[9px] font-mono font-bold bg-[var(--accent-blue)] text-white shadow-sm">
                    {item.badge}
                  </span>
                )}

                {item.isLive && (
                  <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#30d158] opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#30d158]"></span>
                  </span>
                )}
              </div>

              <span className={`text-[10px] tracking-tight mt-0.5 ${isActive ? 'font-bold text-[var(--accent-blue)]' : 'font-medium'}`}>
                {item.label}
              </span>

              {isActive && (
                <span className="absolute bottom-0.5 w-6 h-0.5 rounded-full bg-[var(--accent-blue)]" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};
