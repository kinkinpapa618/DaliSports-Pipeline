import React from 'react';
import { Trophy, Clock, Cpu, Share2, Settings, RefreshCw, Mail, Sun, Moon, Zap, Activity } from 'lucide-react';
import { ActiveTab } from '../types';
import { SkinMode } from '../hooks/useSkin';

interface SidebarProps {
  currentTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  tournamentCount: number;
  isPipelineRunning: boolean;
  onRefresh: () => void;
  skin?: SkinMode;
  onToggleSkin?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onTabChange,
  tournamentCount,
  isPipelineRunning,
  onRefresh,
  skin = 'dark',
  onToggleSkin,
}) => {
  const menuItems = [
    {
      id: 'tournaments' as ActiveTab,
      label: 'Giải Đấu & Video',
      icon: Trophy,
      badge: tournamentCount > 0 ? tournamentCount : undefined,
    },
    {
      id: 'timeline' as ActiveTab,
      label: 'Timeline & Tỷ Số',
      icon: Clock,
    },
    {
      id: 'pipeline' as ActiveTab,
      label: 'Pipeline Studio',
      icon: Cpu,
      isLive: isPipelineRunning,
    },
    {
      id: 'seo' as ActiveTab,
      label: 'SEO & Metadata',
      icon: Share2,
    },
    {
      id: 'settings' as ActiveTab,
      label: 'Cài Đặt',
      icon: Settings,
    },
  ];

  return (
    <aside className="hidden md:flex w-64 bg-[var(--bg-sidebar)] border-r border-[var(--border-subtle)] flex-col justify-between select-none transition-colors shrink-0">
      {/* Top Menu */}
      <div className="p-3 space-y-1.5">
        <div className="px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-[var(--text-faint)] flex items-center justify-between">
          <span>ĐIỀU KHIỂN HỆ THỐNG</span>
          <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent-blue)]" />
        </div>

        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-full text-xs font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[var(--bg-element)] text-[var(--accent-blue)] font-bold shadow-[0_2px_10px_rgba(0,0,0,0.08)] border border-[var(--accent-blue)]/25'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-highlight)]'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--accent-blue)]' : 'text-[var(--text-muted)]'}`} />
                <span>{item.label}</span>
              </div>

              {item.badge !== undefined && (
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                  isActive ? 'bg-[var(--accent-blue)] text-white' : 'bg-[var(--bg-highlight)] text-[var(--text-muted)]'
                }`}>
                  {item.badge}
                </span>
              )}

              {item.isLive && (
                <span className="w-2 h-2 rounded-full bg-[#30d158] animate-ping" />
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Actions & Apple Control Center Widget */}
      <div className="p-3 border-t border-[var(--border-subtle)] space-y-2.5">
        {/* Quick Skin Switcher */}
        {onToggleSkin && (
          <button
            onClick={onToggleSkin}
            className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-[var(--bg-element)] hover:bg-[var(--bg-highlight)] text-[var(--text-main)] text-xs font-medium transition-all border border-[var(--border-subtle)] shadow-sm cursor-pointer"
            title="Đổi giao diện nhanh giữa Studio Tối và Apple Sáng"
          >
            <div className="flex items-center gap-2">
              {skin === 'light' ? (
                <Sun className="w-3.5 h-3.5 text-amber-500" />
              ) : (
                <Moon className="w-3.5 h-3.5 text-[var(--accent-blue)]" />
              )}
              <span>Giao Diện:</span>
            </div>
            <span className="font-semibold text-[11px] text-[var(--accent-blue)]">
              {skin === 'light' ? 'Apple Light' : 'Vision Dark'}
            </span>
          </button>
        )}

        <button
          onClick={onRefresh}
          className="w-full flex items-center justify-center gap-2 px-3.5 py-2 rounded-xl bg-[var(--bg-element)] hover:bg-[var(--bg-highlight)] text-[var(--text-main)] text-xs font-medium transition-all border border-[var(--border-subtle)] shadow-sm cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5 text-[var(--text-muted)]" />
          <span>Làm Mới Dữ Liệu</span>
        </button>

        {/* Apple Control Center Style Widget */}
        <div className="control-center !p-3 space-y-0 text-xs">
          <div className="cc-row !py-1.5">
            <div className="cc-icon orange !w-6 !h-6 !text-[11px]">
              <Zap className="w-3.5 h-3.5" />
            </div>
            <div className="flex-1 text-[11px] text-[var(--text-main)] font-medium">Gemini 2.5 AI</div>
            <div className="text-[10px] text-[var(--text-muted)] font-mono">Active</div>
          </div>

          <div className="cc-row !py-1.5">
            <div className="cc-icon blue !w-6 !h-6 !text-[11px]">
              <Activity className="w-3.5 h-3.5" />
            </div>
            <div className="flex-1 text-[11px] text-[var(--text-main)] font-medium">FFmpeg Core</div>
            <div className="text-[10px] text-[#30d158] font-mono">Ready</div>
          </div>
        </div>

        {/* Copyright Footer */}
        <div className="pt-2 px-1 text-center border-t border-[var(--border-subtle)] space-y-0.5">
          <div className="text-[11px] font-medium text-[var(--text-faint)] flex items-center justify-center gap-1">
            <span>© 2026</span>
            <span className="text-[var(--accent-blue)] font-semibold">Hữu Mạnh - BMB</span>
          </div>
          <button
            onClick={() => window.api?.openUrl('mailto:huumanh.info@aol.com')}
            className="text-[10px] text-[var(--text-faint)] hover:text-[var(--accent-blue)] transition-colors flex items-center justify-center gap-1 mx-auto font-mono hover:underline cursor-pointer"
            title="Gửi email cho tác giả"
          >
            <Mail className="w-3 h-3 text-[var(--text-faint)]" />
            <span>huumanh.info@aol.com</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
