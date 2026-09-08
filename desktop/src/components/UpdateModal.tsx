import React, { useState } from 'react';
import { Sparkles, Download, X, Check, ExternalLink, Calendar, HardDrive, ArrowRight, Zap, Loader2, RotateCw, AlertCircle } from 'lucide-react';
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
  const [updateStatus, setUpdateStatus] = useState<'idle' | 'updating' | 'success' | 'error'>('idle');
  const [updateLogs, setUpdateLogs] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string>('');

  if (!isOpen || !updateInfo || !updateInfo.hasUpdate) return null;

  const handleManualDownload = () => {
    if (updateInfo.downloadUrl) {
      window.api?.openUrl(updateInfo.downloadUrl);
    }
  };

  const handleOpenChangelog = () => {
    if (updateInfo.changelogUrl) {
      window.api?.openUrl(updateInfo.changelogUrl);
    }
  };

  const handleAutoUpdate = async () => {
    if (!window.api?.applyUpdate) {
      handleManualDownload();
      return;
    }

    setUpdateStatus('updating');
    setUpdateLogs(['Đang khởi động tiến trình cập nhật tự động...']);
    setErrorMessage('');

    try {
      const result = await window.api.applyUpdate();
      if (result.logs && result.logs.length > 0) {
        setUpdateLogs(result.logs);
      }

      if (result.success) {
        setUpdateStatus('success');
      } else {
        setUpdateStatus('error');
        setErrorMessage(result.message || 'Cập nhật thất bại.');
      }
    } catch (err: any) {
      setUpdateStatus('error');
      setErrorMessage(err?.message || 'Lỗi không xác định khi cập nhật.');
    }
  };

  const handleRestart = () => {
    if (window.api?.restartApp) {
      window.api.restartApp();
    } else {
      window.location.reload();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-4 animate-in fade-in duration-200">
      <div className="apple-card w-full max-w-lg p-6 space-y-5 shadow-2xl animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between pb-3 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-3">
            <div className={`cc-icon !w-10 !h-10 !rounded-xl text-white shadow-lg ${
              updateStatus === 'success' 
                ? 'green shadow-[#30d158]/25' 
                : updateStatus === 'error'
                ? 'red shadow-[#ff453a]/25'
                : 'orange shadow-[#ff9f0a]/20'
            }`}>
              {updateStatus === 'updating' ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : updateStatus === 'success' ? (
                <Check className="w-5 h-5 stroke-[3]" />
              ) : updateStatus === 'error' ? (
                <AlertCircle className="w-5 h-5 stroke-[2.5]" />
              ) : (
                <Sparkles className="w-5 h-5 stroke-[2.5]" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-[var(--text-main)]">
                  {updateStatus === 'success' ? 'Cập Nhật Thành Công!' : 'Có Bản Cập Nhật Mới!'}
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-[#ff9f0a]/15 border border-[#ff9f0a]/30 text-[#ff9f0a] text-[10px] font-mono font-bold">
                  v{updateInfo.latestVersion}
                </span>
              </div>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">
                {updateInfo.title || `DaliSports Studio v${updateInfo.latestVersion}`}
              </p>
            </div>
          </div>

          {updateStatus !== 'updating' && (
            <button
              onClick={onClose}
              className="circle-btn !w-8 !h-8 text-xs cursor-pointer"
              title="Đóng"
            >
              <X className="w-4 h-4" />
            </button>
          )}
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

        {/* Status Views */}
        {updateStatus === 'updating' ? (
          <div className="p-4 rounded-2xl bg-[var(--bg-input)] border border-[var(--accent-blue)]/30 space-y-3">
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 text-[var(--accent-blue)] animate-spin" />
              <div>
                <div className="text-xs font-bold text-[var(--text-main)]">Đang Tự Động Cập Nhật...</div>
                <div className="text-[11px] text-[var(--text-muted)]">Vui lòng không tắt ứng dụng trong quá trình đồng bộ.</div>
              </div>
            </div>
            {updateLogs.length > 0 && (
              <div className="p-2.5 rounded-xl bg-black/40 border border-white/5 font-mono text-[11px] text-emerald-400 space-y-1 max-h-32 overflow-y-auto">
                {updateLogs.map((log, idx) => (
                  <div key={idx} className="leading-tight truncate">{log}</div>
                ))}
              </div>
            )}
          </div>
        ) : updateStatus === 'success' ? (
          <div className="p-4 rounded-2xl bg-[#30d158]/10 border border-[#30d158]/30 space-y-2">
            <div className="flex items-center gap-2 text-[#30d158] font-bold text-xs">
              <Check className="w-4 h-4 stroke-[3]" />
              <span>Đã cập nhật hoàn tất lên phiên bản v{updateInfo.latestVersion}!</span>
            </div>
            <p className="text-[11px] text-[var(--text-muted)]">
              Mã nguồn và hệ thống đã được đồng bộ mới nhất. Hãy bấm nút Khởi Động Lại bên dưới để kích hoạt bản cập nhật ngay lập tức.
            </p>
          </div>
        ) : updateStatus === 'error' ? (
          <div className="p-4 rounded-2xl bg-[#ff453a]/10 border border-[#ff453a]/30 space-y-2">
            <div className="flex items-center gap-2 text-[#ff453a] font-bold text-xs">
              <AlertCircle className="w-4 h-4" />
              <span>Cập nhật tự động gặp sự cố</span>
            </div>
            <p className="text-[11px] text-[var(--text-main)] font-mono">{errorMessage}</p>
            <p className="text-[10px] text-[var(--text-muted)]">
              Bạn vẫn có thể tải bản phát hành thủ công hoặc sử dụng file <code>update.bat</code>.
            </p>
          </div>
        ) : (
          /* Release Notes */
          updateInfo.releaseNotes && updateInfo.releaseNotes.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-[var(--text-main)]">
                Điểm mới & Cải tiến trong bản v{updateInfo.latestVersion}:
              </div>
              <div className="max-h-44 overflow-y-auto space-y-1.5 pr-1">
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
          )
        )}

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-[var(--border-subtle)]">
          {updateInfo.changelogUrl ? (
            <button
              onClick={handleOpenChangelog}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--accent-blue)] flex items-center gap-1 transition-colors hover:underline cursor-pointer"
            >
              <span>Xem Changelog GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2 w-full sm:w-auto">
            {updateStatus === 'success' ? (
              <button
                onClick={handleRestart}
                className="w-full sm:w-auto px-5 py-2.5 rounded-full bg-[#30d158] hover:bg-[#28b84c] text-slate-950 font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-[#30d158]/30 transition-all cursor-pointer"
              >
                <RotateCw className="w-4 h-4" />
                <span>Khởi Động Lại Ngay</span>
              </button>
            ) : updateStatus === 'updating' ? (
              <div className="text-xs text-[var(--text-muted)] font-mono animate-pulse">
                Đang xử lý...
              </div>
            ) : (
              <>
                <button
                  onClick={onClose}
                  className="flex-1 sm:flex-initial px-4 py-2 rounded-full bg-[#242c36] hover:bg-[#2e3743] text-xs font-medium text-[var(--text-main)] border border-white/5 transition-colors cursor-pointer"
                >
                  Để Sau
                </button>
                <button
                  onClick={handleAutoUpdate}
                  className="btn-blue cursor-pointer font-bold flex items-center gap-1.5 shadow-lg shadow-[#0a84ff]/30"
                  title="Cập nhật trực tiếp 1-click không cần tải zip"
                >
                  <Zap className="w-4 h-4 fill-current stroke-[2.5]" />
                  <span>Cập Nhật Ngay</span>
                </button>
                <button
                  onClick={handleManualDownload}
                  className="p-2 rounded-full bg-[#242c36] hover:bg-[#2e3743] text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors cursor-pointer"
                  title="Tải thủ công qua trình duyệt"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
