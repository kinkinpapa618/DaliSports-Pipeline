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
    <div className="titlebar-drag-region h-11 bg-[#101418] border-b border-[#1e252e] flex items-center justify-between px-3 select-none z-50 transition-colors">
      {/* Brand & Status */}
      <div className="flex items-center gap-2.5">
        <img src={logoSymbol} alt="DaliSports" className="w-5 h-5 object-contain drop-shadow" />
        <span className="font-bold text-xs tracking-wider text-[#e2e8f0]">
          DALISPORTS <span className="text-[#0a84ff] font-semibold">STUDIO</span>
        </span>
        <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#181e25] text-[#8492a6] font-mono border border-white/5">
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
            className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-medium transition-all border shadow-sm ${
              skin === 'light'
                ? 'bg-slate-100 hover:bg-slate-200 text-slate-800 border-slate-300'
                : 'bg-[#181e25] hover:bg-[#222a33] text-[#e2e8f0] border-white/5 shadow-[0_2px_8px_rgba(0,0,0,0.25)]'
            }`}
            title={skin === 'light' ? 'Chuyển sang Giao diện Studio Tối (Dark)' : 'Chuyển sang Giao diện Apple Sáng (Light - Clear - Basic)'}
          >
            {skin === 'light' ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-500 fill-amber-500/20" />
                <span className="text-[10px] font-semibold text-slate-800">Apple Light</span>
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
            className="w-8 h-7 flex items-center justify-center text-[#8492a6] hover:text-[#e2e8f0] hover:bg-[#1f252d] transition-colors rounded-md"
            title="Thu nhỏ"
          >
            <Minus className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={handleMaximize}
            className="w-8 h-7 flex items-center justify-center text-[#8492a6] hover:text-[#e2e8f0] hover:bg-[#1f252d] transition-colors rounded-md"
            title="Phóng to / Thu lại"
          >
            <Square className="w-3 h-3" />
          </button>
          <button
            onClick={handleClose}
            className="w-8 h-7 flex items-center justify-center text-[#8492a6] hover:text-white hover:bg-[#ff453a] transition-colors rounded-md"
            title="Đóng ứng dụng"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
