import React, { useState, useEffect } from 'react';
import { 
  Settings, Key, Video, Globe, HardDrive, 
  CheckCircle, AlertCircle, Shield, FolderOpen, Save,
  Eye, EyeOff, ExternalLink, RefreshCw, Sparkles, Sun, Moon,
  ArrowUpCircle, Download, Zap, Loader2, RotateCw,
  Wifi, Copy, Check, QrCode
} from 'lucide-react';
import { EnvConfig, UpdateCheckResult } from '../types';
import { SkinMode } from '../hooks/useSkin';

interface SettingsViewProps {
  skin?: SkinMode;
  onSetSkin?: (mode: SkinMode) => void;
  onUpdateDetected?: (info: UpdateCheckResult) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ 
  skin = 'dark', 
  onSetSkin,
  onUpdateDetected,
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Form State
  const [geminiApiKey, setGeminiApiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash-lite');
  const [fbPageId, setFbPageId] = useState('');
  const [fbAccessToken, setFbAccessToken] = useState('');
  const [updateUrl, setUpdateUrl] = useState('');

  // Update State
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const [updateResult, setUpdateResult] = useState<UpdateCheckResult | null>(null);
  const [currentAppVersion, setCurrentAppVersion] = useState('1.1.0');

  // Toggles for password masking
  const [showGeminiKey, setShowGeminiKey] = useState(false);
  const [showFbToken, setShowFbToken] = useState(false);

  // Updates apply state
  const [isApplyingUpdate, setIsApplyingUpdate] = useState(false);
  const [applyUpdateSuccess, setApplyUpdateSuccess] = useState(false);
  const [applyUpdateError, setApplyUpdateError] = useState('');

  const handleApplyUpdate = async () => {
    if (!window.api?.applyUpdate) return;
    setIsApplyingUpdate(true);
    setApplyUpdateError('');
    try {
      const res = await window.api.applyUpdate();
      if (res.success) {
        setApplyUpdateSuccess(true);
      } else {
        setApplyUpdateError(res.message);
      }
    } catch (err: any) {
      setApplyUpdateError(err?.message || 'Lỗi cập nhật');
    } finally {
      setIsApplyingUpdate(false);
    }
  };

  const handleRestart = () => {
    if (window.api?.restartApp) {
      window.api.restartApp();
    } else {
      window.location.reload();
    }
  };

  // Remote Tunnel State
  const [tunnelRunning, setTunnelRunning] = useState(false);
  const [tunnelUrl, setTunnelUrl] = useState<string | null>(null);
  const [tunnelLoading, setTunnelLoading] = useState(false);
  const [tunnelError, setTunnelError] = useState<string | null>(null);
  const [copiedUrl, setCopiedUrl] = useState(false);

  const checkTunnelStatus = async () => {
    if (window.api?.getTunnelStatus) {
      try {
        const s = await window.api.getTunnelStatus();
        setTunnelRunning(Boolean(s.active));
        setTunnelUrl(s.url || null);
        if (s.error) setTunnelError(s.error);
      } catch {}
    }
  };

  const handleToggleTunnel = async () => {
    setTunnelLoading(true);
    setTunnelError(null);
    try {
      if (tunnelRunning) {
        if (window.api?.stopTunnel) {
          await window.api.stopTunnel();
          setTunnelRunning(false);
          setTunnelUrl(null);
        }
      } else {
        if (window.api?.startTunnel) {
          const res = await window.api.startTunnel();
          if (res.success && res.url) {
            setTunnelRunning(true);
            setTunnelUrl(res.url);
          } else {
            setTunnelError(res.error || 'Không thể khởi động Cloudflare Tunnel');
          }
        }
      }
    } catch (err: any) {
      setTunnelError(err?.message || 'Lỗi khi khởi chạy Tunnel');
    } finally {
      setTunnelLoading(false);
    }
  };

  const handleCopyUrl = (url: string) => {
    navigator.clipboard.writeText(url);
    setCopiedUrl(true);
    setTimeout(() => setCopiedUrl(false), 2500);
  };

  // File status
  const [status, setStatus] = useState<Partial<EnvConfig>>({
    hasCookiesTxt: false,
    hasClientSecrets: false,
    hasYoutubeToken: false,
  });

  const loadConfig = async () => {
    setLoading(true);
    try {
      checkTunnelStatus();
      if (window.api && typeof window.api.getConfig === 'function') {
        const conf: EnvConfig = await window.api.getConfig();
        if (conf) {
          setGeminiApiKey(conf.GEMINI_API_KEY || '');
          setGeminiModel(conf.GEMINI_MODEL || 'gemini-2.5-flash-lite');
          setFbPageId(conf.FB_PAGE_ID || '');
          setFbAccessToken(conf.FB_PAGE_ACCESS_TOKEN || '');
          setUpdateUrl(conf.UPDATE_CHECK_URL || '');
          setStatus({
            hasCookiesTxt: conf.hasCookiesTxt,
            hasClientSecrets: conf.hasClientSecrets,
            hasYoutubeToken: conf.hasYoutubeToken,
          });
        }
      }

      if (window.api && typeof window.api.getCurrentVersion === 'function') {
        const v = await window.api.getCurrentVersion();
        if (v) setCurrentAppVersion(v);
      }
    } catch (err) {
      console.error('Lỗi khi tải cấu hình:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckUpdates = async () => {
    setCheckingUpdate(true);
    try {
      if (window.api && typeof window.api.checkForUpdates === 'function') {
        const res = await window.api.checkForUpdates(updateUrl.trim() || undefined);
        setUpdateResult(res);
        if (res && res.hasUpdate && onUpdateDetected) {
          onUpdateDetected(res);
        }
      }
    } catch (err: any) {
      setUpdateResult({
        hasUpdate: false,
        currentVersion: currentAppVersion,
        latestVersion: currentAppVersion,
        checkedAt: new Date().toISOString(),
        error: err?.message || 'Lỗi khi kiểm tra bản cập nhật',
      });
    } finally {
      setCheckingUpdate(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);

    try {
      if (window.api && typeof window.api.saveConfig === 'function') {
        const ok = await window.api.saveConfig({
          GEMINI_API_KEY: geminiApiKey.trim(),
          GEMINI_MODEL: geminiModel.trim(),
          FB_PAGE_ID: fbPageId.trim(),
          FB_PAGE_ACCESS_TOKEN: fbAccessToken.trim(),
          UPDATE_CHECK_URL: updateUrl.trim(),
        });

        if (ok) {
          setSaveSuccess(true);
          setTimeout(() => setSaveSuccess(false), 4000);
        }
      }
    } catch (err) {
      console.error('Lỗi khi lưu cấu hình:', err);
    } finally {
      setSaving(false);
    }
  };

  const openUrl = (url: string) => {
    window.api?.openUrl(url);
  };

  return (
    <div className="h-full flex flex-col p-3 sm:p-6 space-y-3.5 sm:space-y-5 overflow-y-auto">
      {/* Header */}
      <div className="apple-card p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="cc-icon blue !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Settings className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-[var(--text-main)]">Cài Đặt Hệ Thống & Cấu Hình .ENV</h1>
            <p className="text-xs text-[var(--text-muted)]">
              Quản lý API Key Google Gemini, chứng thực Facebook Fanpage, YouTube OAuth và các tham số pipeline
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadConfig}
            className="circle-btn !w-9 !h-9 text-xs"
            title="Tải lại cài đặt từ file .env"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={handleSave}
            disabled={saving}
            className={`btn-blue !py-2 !px-4 text-xs font-bold transition-all shadow-lg cursor-pointer ${
              saveSuccess
                ? '!bg-[#30d158] text-slate-950 !shadow-[0_5px_15px_rgba(48,209,88,0.35)]'
                : ''
            }`}
          >
            {saveSuccess ? (
              <>
                <CheckCircle className="w-4 h-4 stroke-[3]" />
                <span>Đã Lưu .ENV Thành Công!</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>{saving ? 'Đang Lưu...' : 'Lưu Cấu Hình (.ENV)'}</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* App Skin & Theme Selector */}
      <div className="apple-card p-5 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#ff9f0a]" />
            <h3 className="text-xs font-bold text-[var(--text-main)]">Chủ Đề & Giao Diện Ứng Dụng (App Skins)</h3>
          </div>
          <span className="text-[11px] text-[var(--text-muted)] font-mono">
            Đang kích hoạt: <strong className="text-[var(--accent-blue)] font-bold">{skin === 'light' ? 'Apple Light (Clear - Basic)' : 'Vision Dark (Apple Dark System)'}</strong>
          </span>
        </div>

        <p className="text-xs text-[var(--text-muted)]">
          Lựa chọn phong cách hiển thị phù hợp với môi trường và sở thích làm việc. Cài đặt được lưu tự động trên máy tính.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          {/* Option 1: Vision Dark (Apple Dark System) */}
          <div
            onClick={() => onSetSkin && onSetSkin('dark')}
            className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
              skin === 'dark'
                ? 'border-[#0a84ff] bg-[#14181d] shadow-lg shadow-[#0a84ff]/15 ring-1 ring-[#0a84ff]/30'
                : 'border-[var(--border-subtle)] bg-[var(--bg-element)]/50 hover:border-white/20'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-[var(--bg-input)] flex items-center justify-center text-[#0a84ff] border border-[var(--border-subtle)]">
                  <Moon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-[var(--text-main)]">Vision Dark</div>
                  <div className="text-[10px] text-[var(--text-muted)]">Phong cách Apple Dark / VisionOS (#101418 / #14181d)</div>
                </div>
              </div>
              {skin === 'dark' && (
                <CheckCircle className="w-5 h-5 text-[#0a84ff] shrink-0" />
              )}
            </div>

            {/* Mini Visual Preview */}
            <div className="h-12 rounded-xl bg-[#14181d] border border-[var(--border-subtle)] p-2 flex items-center gap-2">
              <div className="w-8 h-full rounded-lg bg-[#101418] border border-[var(--border-subtle)]" />
              <div className="flex-1 h-full flex flex-col justify-between py-0.5">
                <div className="w-2/3 h-2 rounded bg-[#1f252d]" />
                <div className="w-full h-1.5 rounded bg-[#0a84ff]/50" />
              </div>
            </div>
          </div>

          {/* Option 2: Apple Light */}
          <div
            onClick={() => onSetSkin && onSetSkin('light')}
            className={`p-4 rounded-2xl border-2 transition-all cursor-pointer flex flex-col justify-between space-y-3 ${
              skin === 'light'
                ? 'border-[#0a84ff] bg-white shadow-lg shadow-[#0a84ff]/15 ring-1 ring-[#0a84ff]/30'
                : 'border-[var(--border-subtle)] bg-[var(--bg-element)]/50 hover:border-white/20'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/15 border border-amber-500/30 flex items-center justify-center text-amber-500">
                  <Sun className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-800">Apple Light (Clear - Basic)</div>
                  <div className="text-[10px] text-slate-500">Trắng sáng tinh khôi, tối giản chuẩn Apple</div>
                </div>
              </div>
              {skin === 'light' && (
                <CheckCircle className="w-5 h-5 text-[#0a84ff] shrink-0" />
              )}
            </div>

            {/* Mini Visual Preview */}
            <div className="h-12 rounded-lg bg-[#f5f5f7] border border-[#e5e5ea] p-2 flex items-center gap-2">
              <div className="w-8 h-full rounded bg-[#ffffff] border border-[#e5e5ea]" />
              <div className="flex-1 h-full flex flex-col justify-between py-0.5">
                <div className="w-2/3 h-2 rounded bg-[#e5e5ea]" />
                <div className="w-full h-1.5 rounded bg-[#0071e3]/50" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* App Version & Updates Card */}
      <div className="apple-card p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#3a4750] gap-3">
          <div className="flex items-center gap-2.5">
            <div className="cc-icon green !w-8 !h-8 !rounded-lg text-white">
              <ArrowUpCircle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[#e0e0e0]">Cập Nhật & Phiên Bản Ứng Dụng (App Updates)</h3>
              <p className="text-[10px] text-[#808890]">
                Kiểm tra bản cập nhật mới, xem ghi chú phát hành (Release Notes) và tải bộ cài đặt mới nhất
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] px-3 py-1 rounded-full bg-[#14181d] border border-white/5 font-mono text-[#808890]">
              Hiện tại: <strong className="text-[#0a84ff]">v{currentAppVersion}</strong>
            </span>
            <button
              type="button"
              onClick={handleCheckUpdates}
              disabled={checkingUpdate}
              className="btn-blue !py-1.5 !px-3.5 text-xs font-bold transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${checkingUpdate ? 'animate-spin' : ''}`} />
              <span>{checkingUpdate ? 'Đang Kiểm Tra...' : 'Kiểm Tra Bản Mới'}</span>
            </button>
          </div>
        </div>

        {/* Update Status Result Banner */}
        {updateResult && (
          <div className="space-y-3 animate-in fade-in duration-200">
            {updateResult.hasUpdate ? (
              <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-transparent border border-emerald-500/30 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
                    <span className="text-xs font-bold text-emerald-300">
                      Đã có phiên bản mới: v{updateResult.latestVersion}
                    </span>
                    {updateResult.releaseDate && (
                      <span className="text-[10px] font-mono text-slate-400">
                        ({updateResult.releaseDate})
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {applyUpdateSuccess ? (
                      <button
                        type="button"
                        onClick={handleRestart}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#30d158] hover:bg-[#28b84c] text-slate-950 font-bold text-xs shadow-md shadow-[#30d158]/30 transition-all cursor-pointer w-fit"
                      >
                        <RotateCw className="w-3.5 h-3.5" />
                        <span>Khởi Động Lại Ngay</span>
                      </button>
                    ) : (
                      <>
                        <button
                          type="button"
                          disabled={isApplyingUpdate}
                          onClick={handleApplyUpdate}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-xs shadow-md transition-all cursor-pointer w-fit"
                          title="Cập nhật tự động mã nguồn và hệ thống mà không cần mở trình duyệt"
                        >
                          {isApplyingUpdate ? (
                            <>
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              <span>Đang Cập Nhật...</span>
                            </>
                          ) : (
                            <>
                              <Zap className="w-3.5 h-3.5 fill-current stroke-[2.5]" />
                              <span>⚡ Cập Nhật Tự Động</span>
                            </>
                          )}
                        </button>
                        {updateResult.downloadUrl && (
                          <button
                            type="button"
                            onClick={() => window.api?.openUrl(updateResult.downloadUrl!)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
                            title="Tải gói zip thủ công qua trình duyệt"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {applyUpdateSuccess && (
                  <div className="p-2.5 rounded-lg bg-[#30d158]/15 border border-[#30d158]/30 text-[#30d158] text-xs flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 shrink-0" />
                    <span>Hệ thống đã cập nhật thành công! Bấm "Khởi Động Lại Ngay" để áp dụng.</span>
                  </div>
                )}

                {applyUpdateError && (
                  <div className="p-2.5 rounded-lg bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>Lỗi: {applyUpdateError}</span>
                  </div>
                )}

                {updateResult.releaseNotes && updateResult.releaseNotes.length > 0 && (
                  <div className="pt-2 border-t border-emerald-500/20 space-y-1">
                    <div className="text-[11px] font-semibold text-slate-300">Tính năng & Sửa lỗi mới:</div>
                    <ul className="space-y-1">
                      {updateResult.releaseNotes.map((note, i) => (
                        <li key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                          <span className="text-emerald-400 mt-0.5 font-bold">•</span>
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : updateResult.error ? (
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{updateResult.error}</span>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 text-xs flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>Bạn đang sử dụng phiên bản mới nhất (<strong>v{updateResult.currentVersion}</strong>). Không có bản cập nhật nào.</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  Kiểm tra lúc: {new Date(updateResult.checkedAt).toLocaleTimeString()}
                </span>
              </div>
            )}
          </div>
        )}

        {/* Custom Update URL Field */}
        <div className="pt-2 border-t border-slate-800/80">
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            URL Máy Chủ Cập Nhật (UPDATE_CHECK_URL - Tùy chọn):
          </label>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <input
              type="text"
              value={updateUrl}
              onChange={(e) => setUpdateUrl(e.target.value)}
              placeholder="https://raw.githubusercontent.com/kinkinpapa618/DaliSports-Pipeline/main/version.json"
              className="flex-1 px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-blue)]"
            />
            <button
              type="button"
              onClick={() => openUrl('https://github.com/kinkinpapa618/DaliSports-Pipeline/releases')}
              className="px-3 py-2 rounded-lg bg-[#242c36] hover:bg-[#2e3743] text-[var(--text-main)] text-xs flex items-center justify-center gap-1.5 border border-white/5 transition-colors shrink-0 cursor-pointer"
              title="Mở trang GitHub Releases"
            >
              <span>GitHub Releases</span>
              <ExternalLink className="w-3 h-3" />
            </button>
          </div>
          <p className="text-[10px] text-[var(--text-faint)] mt-1">
            Mặc định hệ thống sẽ kiểm tra tệp <code>version.json</code> trên repository để xác định bản cập nhật mới.
          </p>
        </div>
      </div>

      {/* Remote Access & Cloudflare Tunnel Card */}
      <div className="apple-card p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-xl flex items-center justify-center border border-[var(--border-subtle)] ${
              tunnelRunning ? 'bg-[#30d158]/15 text-[#30d158] border-[#30d158]/30' : 'bg-[var(--bg-input)] text-[var(--text-muted)]'
            }`}>
              <Wifi className={`w-4 h-4 ${tunnelRunning ? 'animate-pulse' : ''}`} />
            </div>
            <div>
              <h3 className="text-xs font-bold text-[var(--text-main)]">Truy Cập Từ Xa (Remote Access & Cloudflare Tunnel)</h3>
              <p className="text-[11px] text-[var(--text-muted)]">
                Tạo tên miền tunnel bảo mật để mở và điều khiển DaliSports Studio từ điện thoại, iPad hoặc máy tính khác
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className={`px-2.5 py-1 rounded-full text-[10px] font-mono font-bold flex items-center gap-1.5 border ${
              tunnelRunning 
                ? 'bg-[#30d158]/15 border-[#30d158]/30 text-[#30d158]' 
                : 'bg-[var(--bg-input)] border-[var(--border-subtle)] text-[var(--text-muted)]'
            }`}>
              <span className={`w-2 h-2 rounded-full ${tunnelRunning ? 'bg-[#30d158] animate-ping' : 'bg-slate-500'}`} />
              <span>{tunnelRunning ? 'ĐANG PHÁT SÓNG TỪ XA' : 'CHƯA KÍCH HOẠT'}</span>
            </span>

            <button
              type="button"
              disabled={tunnelLoading}
              onClick={handleToggleTunnel}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer ${
                tunnelRunning
                  ? 'bg-rose-600 hover:bg-rose-500 text-white'
                  : 'btn-blue !shadow-[0_4px_12px_rgba(10,132,255,0.3)]'
              }`}
            >
              {tunnelLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Đang xử lý...</span>
                </>
              ) : tunnelRunning ? (
                <span>Tắt Tunnel</span>
              ) : (
                <>
                  <Globe className="w-3.5 h-3.5" />
                  <span>Bật Truy Cập Từ Xa</span>
                </>
              )}
            </button>
          </div>
        </div>

        {tunnelError && (
          <div className="p-3 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>Lỗi: {tunnelError}</span>
          </div>
        )}

        {tunnelRunning && tunnelUrl ? (
          <div className="p-4 rounded-2xl bg-gradient-to-r from-[#0a84ff]/10 via-emerald-500/5 to-transparent border border-[#0a84ff]/30 space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="text-[11px] font-semibold text-[var(--accent-blue)] flex items-center gap-1.5">
                  <Globe className="w-3.5 h-3.5" />
                  <span>Đường Dẫn Truy Cập Từ Xa Của Bạn:</span>
                </div>
                <div className="text-sm font-mono font-bold text-[var(--text-main)] select-all break-all">
                  {tunnelUrl}
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleCopyUrl(tunnelUrl)}
                  className="px-3.5 py-1.5 rounded-xl bg-[var(--bg-input)] hover:bg-[var(--bg-highlight)] text-[var(--text-main)] text-xs font-medium border border-[var(--border-subtle)] flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  {copiedUrl ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-[#30d158]" />
                      <span className="text-[#30d158]">Đã Sao Chép!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-[var(--text-muted)]" />
                      <span>Sao Chép Link</span>
                    </>
                  )}
                </button>

                <button
                  type="button"
                  onClick={() => window.api?.openUrl(tunnelUrl)}
                  className="px-3.5 py-1.5 rounded-xl bg-[var(--accent-blue)] hover:brightness-110 text-white text-xs font-bold flex items-center gap-1.5 shadow-md shadow-[#0a84ff]/25 transition-all cursor-pointer"
                >
                  <span>Mở Trình Duyệt</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <div className="pt-3 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-center gap-4">
              <div className="bg-white p-2 rounded-xl shadow-md shrink-0">
                <img
                  src={`https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(tunnelUrl)}`}
                  alt="Mã QR Truy Cập Từ Xa"
                  className="w-28 h-28 object-contain"
                />
              </div>
              <div className="space-y-1 text-xs text-[var(--text-muted)]">
                <div className="font-semibold text-[var(--text-main)] flex items-center gap-1.5">
                  <QrCode className="w-4 h-4 text-[#ff9f0a]" />
                  <span>Quét mã QR bằng Camera điện thoại:</span>
                </div>
                <p>1. Mở ứng dụng Camera trên iPhone hoặc Android và hướng vào mã QR bên cạnh.</p>
                <p>2. Nhấn vào liên kết thông báo xuất hiện trên màn hình để mở ngay bảng điều khiển DaliSports Studio.</p>
                <p>3. Bạn có thể thêm trang web vào màn hình chính (Add to Home Screen) để sử dụng như một App độc lập.</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-3.5 bg-[var(--bg-input)] rounded-xl border border-[var(--border-subtle)] flex items-center justify-between text-xs">
            <div className="space-y-0.5">
              <span className="text-[var(--text-muted)]">Cơ chế bảo mật Cloudflare Tunnel:</span>
              <p className="text-[11px] text-[var(--text-faint)]">
                Không cần mở cổng Modem (No Port Forwarding), hỗ trợ HTTPS SSL tự động, bảo vệ an toàn địa chỉ IP gốc của máy tính.
              </p>
            </div>
            <div className="text-[11px] font-mono text-[var(--text-muted)] shrink-0 pl-3">
              Port: 8000 (API & Web)
            </div>
          </div>
        )}
      </div>

      {/* Main Settings Form */}
      <form onSubmit={handleSave} className="space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Google Gemini AI Configuration */}
          <div className="apple-card p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Key className="w-4 h-4 text-[var(--accent-blue)]" />
                <h3 className="text-xs font-bold text-[var(--text-main)]">Google Gemini AI</h3>
              </div>
              <button
                type="button"
                onClick={() => openUrl('https://aistudio.google.com/')}
                className="text-[11px] text-[var(--accent-blue)] hover:underline flex items-center gap-1"
              >
                <span>Lấy Key Miễn Phí</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                GEMINI_API_KEY:
              </label>
              <div className="relative">
                <input
                  type={showGeminiKey ? 'text' : 'password'}
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  placeholder="AIzaSy..."
                  className="w-full pl-3 pr-10 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-blue)]"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-main)] p-1"
                >
                  {showGeminiKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="text-[10px] text-[var(--text-faint)] mt-1">
                Dùng để phân tích khung hình video và bóc tách bảng điểm tỷ số từng trận.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                GEMINI_MODEL:
              </label>
              <select
                value={geminiModel}
                onChange={(e) => setGeminiModel(e.target.value)}
                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-blue)]"
              >
                <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite (Khuyên dùng: Siêu tốc & Tiết kiệm Quota)</option>
                <option value="gemini-2.5-flash">gemini-2.5-flash (Cân bằng & Độ chính xác cao)</option>
                <option value="gemini-2.0-flash">gemini-2.0-flash</option>
                <option value="gemini-1.5-flash">gemini-1.5-flash</option>
                <option value="gemini-3.6-flash">gemini-3.6-flash</option>
              </select>
            </div>
          </div>

          {/* Facebook Business API Configuration */}
          <div className="apple-card p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-[#0a84ff]" />
                <h3 className="text-xs font-bold text-[var(--text-main)]">Facebook Graph API</h3>
              </div>
              <button
                type="button"
                onClick={() => openUrl('https://developers.facebook.com/tools/explorer/')}
                className="text-[11px] text-[#0a84ff] hover:underline flex items-center gap-1"
              >
                <span>Graph API Explorer</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                FB_PAGE_ID:
              </label>
              <input
                type="text"
                value={fbPageId}
                onChange={(e) => setFbPageId(e.target.value)}
                placeholder="ID Fanpage của bạn (VD: 100092837461928)"
                className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                FB_PAGE_ACCESS_TOKEN:
              </label>
              <div className="relative">
                <input
                  type={showFbToken ? 'text' : 'password'}
                  value={fbAccessToken}
                  onChange={(e) => setFbAccessToken(e.target.value)}
                  placeholder="EAAG..."
                  className="w-full pl-3 pr-10 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-mono focus:outline-none focus:border-[var(--accent-blue)]"
                />
                <button
                  type="button"
                  onClick={() => setShowFbToken(!showFbToken)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-main)] p-1"
                >
                  {showFbToken ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
              <p className="text-[10px] text-[var(--text-faint)] mt-1">
                Token vĩnh viễn quyền <code>pages_manage_posts</code> để đăng video trực tiếp qua API.
              </p>
            </div>
          </div>

          {/* YouTube OAuth Status */}
          <div className="apple-card p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Video className="w-4 h-4 text-[#ff453a]" />
                <h3 className="text-xs font-bold text-[var(--text-main)]">YouTube Data API v3</h3>
              </div>
              {status.hasClientSecrets ? (
                <span className="flex items-center gap-1 text-[11px] text-[#30d158] font-mono">
                  <CheckCircle className="w-3.5 h-3.5" />
                  <span>client_secrets.json OK</span>
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[11px] text-[#ff9f0a] font-mono">
                  <AlertCircle className="w-3.5 h-3.5" />
                  <span>Chưa có client_secrets.json</span>
                </span>
              )}
            </div>

            <p className="text-xs text-[var(--text-muted)]">
              Tệp <code>client_secrets.json</code> được đặt tại thư mục gốc để cấp quyền upload video YouTube qua OAuth 2.0.
            </p>

            <div className="p-3 bg-[var(--bg-input)] rounded-lg border border-[var(--border-subtle)] space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">OAuth Credentials:</span>
                <span className={`font-mono ${status.hasClientSecrets ? 'text-[#30d158]' : 'text-[var(--text-muted)]'}`}>
                  {status.hasClientSecrets ? 'client_secrets.json (Có sẵn)' : 'Thiếu file'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">OAuth Saved Token:</span>
                <span className={`font-mono ${status.hasYoutubeToken ? 'text-[#30d158]' : 'text-[var(--text-muted)]'}`}>
                  {status.hasYoutubeToken ? 'yt_profile/upload_youtube_oauth.json (Đã đăng nhập)' : 'Chưa đăng nhập'}
                </span>
              </div>
            </div>
          </div>

          {/* System & Tools Verification */}
          <div className="apple-card p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-[#bf5af2]" />
                <h3 className="text-xs font-bold text-[var(--text-main)]">Hạ Tầng Công Cụ Hệ Thống</h3>
              </div>
              <span className="flex items-center gap-1 text-[11px] text-[#30d158] font-mono">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Hoạt Động</span>
              </span>
            </div>

            <p className="text-xs text-[var(--text-muted)]">
              Các công cụ xử lý video, tải nguồn và tự động hóa trình duyệt đã tích hợp.
            </p>

            <div className="p-3 bg-[var(--bg-input)] rounded-lg border border-[var(--border-subtle)] space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">FFmpeg Engine:</span>
                <span className="font-mono text-[#30d158]">GPU Accelerated (Copy mode)</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">cookies.txt (Tải Video FB/YT):</span>
                <span className={`font-mono ${status.hasCookiesTxt ? 'text-[#30d158]' : 'text-[#ff9f0a]'}`}>
                  {status.hasCookiesTxt ? 'cookies.txt (Sẵn sàng)' : 'Thiếu cookies.txt'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">Python Runtime:</span>
                <span className="font-mono text-[var(--text-main)]">Python 3.12 (UTF-8 Enforced)</span>
              </div>
            </div>
          </div>

          {/* Copyright & Author Card */}
          <div className="apple-card p-5 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[var(--accent-blue)]" />
                <h3 className="text-xs font-bold text-[var(--text-main)]">Thông Tin Bản Quyền & Tác Giả</h3>
              </div>
              <span className="text-[11px] text-[var(--accent-blue)] font-mono">v{currentAppVersion}</span>
            </div>

            <div className="p-3.5 bg-[var(--bg-input)] rounded-lg border border-[var(--border-subtle)] space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">Bản quyền phần mềm:</span>
                <span className="font-semibold text-[var(--accent-blue)]">Hữu Mạnh - BMB</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)]">Email liên hệ:</span>
                <button
                  type="button"
                  onClick={() => openUrl('mailto:huumanh.info@aol.com')}
                  className="font-mono text-[var(--text-main)] hover:text-[var(--accent-blue)] transition-colors underline"
                >
                  huumanh.info@aol.com
                </button>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-[var(--border-subtle)] text-[11px]">
                <span className="text-[var(--text-faint)]">Phát hành:</span>
                <span className="text-[var(--text-faint)]">Copyright © 2026 Hữu Mạnh - BMB. All rights reserved.</span>
              </div>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};
