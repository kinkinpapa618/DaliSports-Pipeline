import React from 'react';
import { Minus, Square, X, Activity, Sun, Moon, Sparkles } from 'lucide-react';
import logoSymbol from '../assets/logo_symbol.png';
import { SkinMode } from '../hooks/useSkin';
import { UpdateCheckResult } from '../types';

interface TitleBarProps {
  isPipelineRunning?: boolean;
  skin?: SkinMode;
  onToggleSkin?: () => void;
  updateInfo?: UpdateCheckResult | null;
  onOpenUpdateModal?: () => void;
}

export const TitleBar: React.FC<TitleBarProps> = ({ 
  isPipelineRunning,
  skin = 'dark',
  onToggleSkin,
  updateInfo,
  onOpenUpdateModal,
}) => {
  const handleMinimize = () => window.api?.windowMinimize();
  const handleMaximize = () => window.api?.windowMaximize();
  const handleClose = () => window.api?.windowClose();

  return (
    <div className="titlebar-drag-region h-11 bg-[var(--bg-sidebar)] border-b border-[var(--border-subtle)] flex items-center justify-between px-3 select-none z-50 transition-colors">
      {/* Brand & Status */}
      <div className="flex items-center gap-2.5">
        <img src={logoSymbol} alt="DaliSports" className="w-5 h-5 object-contain drop-shadow" />
        <span className="font-bold text-xs tracking-wider text-[var(--text-main)]">
          DALISPORTS <span className="text-[var(--accent-blue)] font-semibold">STUDIO</span>
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-highlight)] text-[var(--text-muted)] font-mono border border-[var(--border-subtle)]">
          v1.0
        </span>
        {updateInfo && updateInfo.hasUpdate && (
          <button
            onClick={onOpenUpdateModal}
            className="titlebar-no-drag flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#ff9f0a] text-white text-[10px] font-bold font-mono shadow-[0_2px_10px_rgba(255,159,10,0.35)] hover:brightness-110 transition-all cursor-pointer animate-pulse"
            title={`Có bản cập nhật mới v${updateInfo.latestVersion}! Nhấn để xem chi tiết`}
          >
            <Sparkles className="w-3 h-3 stroke-[2.5]" />
            <span>Update v{updateInfo.latestVersion}</span>
          </button>
        )}
        {isPipelineRunning && (
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-[#30d158]/15 border border-[#30d158]/30 text-[#30d158] text-[10px] animate-pulse">
            <Activity className="w-3 h-3" />
            <span className="font-medium">PIPELINE RUNNING</span>
          </div>
        )}
      </div>

      {/* Right Controls: Skin Switcher + Window Actions */}
      <div className="titlebar-no-drag flex items-center gap-2.5">
        {/* Apple Style Skin Switcher Toggle */}
        {onToggleSkin && (
          <button
            onClick={onToggleSkin}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium transition-all border shadow-sm cursor-pointer ${
              skin === 'light'
                ? 'bg-white hover:bg-slate-100 text-slate-900 border-[#d2d2d7] shadow-[0_1px_3px_rgba(0,0,0,0.06)]'
                : 'bg-[var(--bg-highlight)] hover:bg-[#2e3844] text-[var(--text-main)] border-white/5 shadow-[0_2px_8px_rgba(0,0,0,0.25)]'
            }`}
            title={skin === 'light' ? 'Chuyển sang Giao diện Studio Tối (Dark)' : 'Chuyển sang Giao diện Apple Sáng (Light - Clear - Basic)'}
          >
            {skin === 'light' ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-500 fill-amber-500/20" />
                <span className="text-[10px] font-bold text-slate-800">Apple Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-[#0a84ff] fill-[#0a84ff]/20" />
                <span className="text-[10px] font-semibold text-[#e2e8f0]">Vision Dark</span>
              </>
            )}
          </button>
        )}

        {/* Window Controls */}
        <div className="flex items-center gap-0.5">
          <button
            onClick={handleMinimize}
            className="w-8 h-7 flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-highlight)] transition-colors rounded-md cursor-pointer"
            title="Thu nhỏ"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleMaximize}
            className="w-8 h-7 flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-highlight)] transition-colors rounded-md cursor-pointer"
            title="Phóng to / Thu lại"
          >
            <Square className="w-3 h-3" />
          </button>
          <button
            onClick={handleClose}
            className="w-8 h-7 flex items-center justify-center text-[var(--text-muted)] hover:text-white hover:bg-[#ff453a] transition-colors rounded-md cursor-pointer"
            title="Đóng ứng dụng"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
