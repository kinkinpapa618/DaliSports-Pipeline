import React from 'react';
import { Sparkles, Download, X, Check, ExternalLink, Calendar, HardDrive, ArrowRight } from 'lucide-react';
import { UpdateCheckResult } from '../types';

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  updateInfo: UpdateCheckResult | null;
}

export const UpdateModal: React.FC<UpdateModalProps> = ({
  isOpen,
  onClose,
  updateInfo,
}) => {
  if (!isOpen || !updateInfo || !updateInfo.hasUpdate) return null;

  const handleDownload = () => {
    if (updateInfo.downloadUrl) {
      window.api?.openUrl(updateInfo.downloadUrl);
    }
  };

  const handleOpenChangelog = () => {
    if (updateInfo.changelogUrl) {
      window.api?.openUrl(updateInfo.changelogUrl);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="apple-card w-full max-w-lg p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3">
            <div className="cc-icon orange !w-10 !h-10 !rounded-xl text-white shadow-lg shadow-[#ff9f0a]/20">
              <Sparkles className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-[var(--text-main)]">Có Bản Cập Nhật Mới!</h3>
                <span className="px-2 py-0.5 rounded-full bg-[#ff9f0a]/15 border border-[#ff9f0a]/30 text-[#ff9f0a] text-[10px] font-mono font-bold">
                  NEW
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                {updateInfo.title || `DaliSports Studio v${updateInfo.latestVersion}`}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="circle-btn !w-8 !h-8 text-xs"
            title="Đóng"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Version Compare Banner */}
        <div className="p-3.5 rounded-2xl bg-[var(--bg-input)] border border-[var(--border-subtle)] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="text-center">
              <div className="text-[10px] text-[var(--text-muted)] font-medium">Hiện Tại</div>
              <div className="text-xs font-mono font-bold text-[var(--text-main)]">v{updateInfo.currentVersion}</div>
            </div>

            <ArrowRight className="w-4 h-4 text-[var(--text-muted)]" />

            <div className="text-center">
              <div className="text-[10px] text-[var(--accent-blue)] font-medium">Mới Nhất</div>
              <div className="text-sm font-mono font-black text-[var(--accent-blue)]">v{updateInfo.latestVersion}</div>
            </div>
          </div>

          <div className="flex items-center gap-3 text-[11px] text-[var(--text-muted)] font-mono">
            {updateInfo.releaseDate && (
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                {updateInfo.releaseDate}
              </span>
            )}
            {updateInfo.packageSize && (
              <span className="flex items-center gap-1">
                <HardDrive className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                {updateInfo.packageSize}
              </span>
            )}
          </div>
        </div>

        {/* Release Notes */}
        {updateInfo.releaseNotes && updateInfo.releaseNotes.length > 0 && (
          <div className="space-y-2">
            <div className="text-xs font-bold text-[var(--text-main)]">
              Điểm mới & Cải tiến trong bản v{updateInfo.latestVersion}:
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
              {updateInfo.releaseNotes.map((note, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs text-[var(--text-main)]">
                  <div className="w-4 h-4 rounded-full bg-[#0a84ff]/15 border border-[#0a84ff]/30 flex items-center justify-center shrink-0 mt-0.5">
                    <Check className="w-2.5 h-2.5 text-[#0a84ff] stroke-[3]" />
                  </div>
                  <span className="leading-relaxed">{note}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-[var(--border-subtle)]">
          {updateInfo.changelogUrl ? (
            <button
              onClick={handleOpenChangelog}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--accent-blue)] flex items-center gap-1 transition-colors hover:underline"
            >
              <span>Xem Changelog GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <button
              onClick={onClose}
              className="flex-1 sm:flex-initial px-4 py-2 rounded-full bg-[#242c36] hover:bg-[#2e3743] text-xs font-medium text-[var(--text-main)] border border-white/5 transition-colors cursor-pointer"
            >
              Để Sau
            </button>
            <button
              onClick={handleDownload}
              className="btn-blue cursor-pointer"
            >
              <Download className="w-4 h-4 stroke-[2.5]" />
              <span>Tải Bản Cập Nhật</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
