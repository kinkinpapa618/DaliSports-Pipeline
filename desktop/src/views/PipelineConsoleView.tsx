import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Square, Terminal, Copy, Trash2, CheckCircle2, 
  AlertCircle, Settings2, Sliders, ShieldAlert, Cpu, UploadCloud,
  Download, Clock, Film, Check, X, Minus, Loader2, Info
} from 'lucide-react';
import { PipelineLogMessage, PipelineOptions, TournamentInfo } from '../types';

interface PipelineConsoleViewProps {
  tournaments: TournamentInfo[];
  selectedTournament: TournamentInfo | null;
  onSelectTournament: (t: TournamentInfo) => void;
  isPipelineRunning: boolean;
  setIsPipelineRunning: (running: boolean) => void;
  initialMode?: 'default' | 'source_yup';
}

export const PipelineConsoleView: React.FC<PipelineConsoleViewProps> = ({
  tournaments,
  selectedTournament,
  onSelectTournament,
  isPipelineRunning,
  setIsPipelineRunning,
  initialMode,
}) => {
  const [logs, setLogs] = useState<PipelineLogMessage[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [copied, setCopied] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(-1); // -1 idle, 0..3 running

  // Xác định log có phải thông báo quan trọng không
  const isImportant = (log: PipelineLogMessage): boolean => {
    if (log.level === 'error' || log.level === 'success') return true;
    if (log.level === 'warn') {
      const m = log.message.toLowerCase();
      // Chỉ giữ warn quan trọng (thất bại, không tìm thấy, bỏ qua bước)
      return m.includes('bỏ qua') || m.includes('không') || m.includes('fail') || m.includes('warn') || m.includes('skip');
    }
    const msg = log.message;
    // Info quan trọng: banner bước, hoàn tất, bắt đầu phiên
    return (
      msg.includes('BẮT ĐẦU') ||
      msg.includes('BƯỚC') ||
      msg.includes('HOÀN TẤT') ||
      msg.includes('SUCCESS') ||
      msg.includes('▶') ||
      msg.includes('[+]') && (msg.includes('Đã lưu') || msg.includes('Phát hiện')) ||
      msg.includes('Đã chèn') ||
      msg.includes('Trận')
    );
  };

  // Form options - 4 bước có thể chạy tuần tự hoặc độc lập
  const [ytUrl, setYtUrl] = useState('');
  const [courtName, setCourtName] = useState('Sân 1');
  const [tournamentName, setTournamentName] = useState('');
  const [sponsor, setSponsor] = useState('');
  const [category, setCategory] = useState('Đôi Nam');
  const [skipDownload, setSkipDownload] = useState(false);
  const [skipTimeline, setSkipTimeline] = useState(false);
  const [skipCut, setSkipCut] = useState(false);
  const [skipUpload, setSkipUpload] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [platform, setPlatform] = useState<'youtube' | 'facebook' | 'both'>('youtube');
  const [ytMode, setYtMode] = useState<'both' | 'source' | 'clips'>('both');

  const logContainerRef = useRef<HTMLDivElement>(null);
  const [showAdvancedMobile, setShowAdvancedMobile] = useState(false);
  const [mobileConfigCollapsed, setMobileConfigCollapsed] = useState(false);

  // Sync selected tournament info with fallback
  useEffect(() => {
    if (selectedTournament) {
      setTournamentName(selectedTournament.name);
    } else if (tournaments && tournaments.length > 0) {
      onSelectTournament(tournaments[0]);
      setTournamentName(tournaments[0].name);
    }
  }, [selectedTournament, tournaments]);

  // Sync initialMode preset
  useEffect(() => {
    if (initialMode === 'source_yup') {
      setYtMode('source');
      setSkipCut(true);
    }
  }, [initialMode, selectedTournament]);

  // Subscribe to logs and exit event safely + suy ra tiến độ bước
  useEffect(() => {
    if (window.api && typeof window.api.onPipelineLog === 'function') {
      window.api.onPipelineLog((log) => {
        if (log) {
          setLogs((prev) => [...prev, log]);
          // Suy ra activeStep từ banner log
          const msg = log.message;
          if (msg.includes('BƯỚC 1') || msg.includes('TẢI VIDEO')) setActiveStep(0);
          else if (msg.includes('BƯỚC 2') || msg.includes('SCAN TIMELINE') || msg.includes('CHUẨN HÓA')) setActiveStep(1);
          else if (msg.includes('BƯỚC 3') && msg.includes('CHUẨN HÓA')) setActiveStep(1);
          else if (msg.includes('BƯỚC 4') || msg.includes('CẮT TỪNG TRẬN') || msg.includes('CẮT')) setActiveStep(2);
          else if (msg.includes('BƯỚC 5') || msg.includes('UPLOAD') || msg.includes('ĐĂNG')) setActiveStep(3);
        }
      });
    }

    if (window.api && typeof window.api.onPipelineExit === 'function') {
      window.api.onPipelineExit((code) => {
        setIsPipelineRunning(false);
        if (code === 0) setActiveStep(-1);
        else if (code !== null) setActiveStep(-2); // error
      });
    }
  }, []);

  // Auto scroll
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Reset progress khi bắt đầu phiên mới
  useEffect(() => {
    if (isPipelineRunning) setActiveStep(0);
  }, [isPipelineRunning]);

  const handleStartPipeline = async (forceSkipCut?: boolean) => {
    if (!selectedTournament) return;

    const options: PipelineOptions = {
      tournamentPath: selectedTournament.path,
      ytUrl: ytUrl.trim() || undefined,
      courtName: courtName.trim() || undefined,
      tournamentName: tournamentName.trim() || undefined,
      sponsor: sponsor.trim() || undefined,
      category: category.trim() || undefined,
      skipDownload,
      skipTimeline,
      skipCut: forceSkipCut !== undefined ? forceSkipCut : skipCut,
      skipUpload,
      dryRun,
      platform,
      ytMode,
    };

    setIsPipelineRunning(true);
    setActiveStep(0);
    setLogs([]);
    setLogs((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        timestamp: new Date().toLocaleTimeString(),
        level: 'info',
        message: `--- BẮT ĐẦU PHIÊN XỬ LÝ [${selectedTournament.name}] ---`,
      },
    ]);

    const started = await window.api.startPipeline(options);
    if (!started) {
      setIsPipelineRunning(false);
      setLogs((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          timestamp: new Date().toLocaleTimeString(),
          level: 'error',
          message: 'Không thể khởi động pipeline. Vui lòng kiểm tra Python và file video nguồn.',
        },
      ]);
    }
  };

  const handleStartSourceYUp = async () => {
    if (!selectedTournament) return;
    setYtMode('source');
    setSkipCut(true);

    const options: PipelineOptions = {
      tournamentPath: selectedTournament.path,
      ytUrl: ytUrl.trim() || undefined,
      courtName: courtName.trim() || undefined,
      tournamentName: tournamentName.trim() || undefined,
      sponsor: sponsor.trim() || undefined,
      category: category.trim() || undefined,
      skipDownload: true,
      skipTimeline: true,
      skipCut: true,
      skipUpload: false,
      dryRun,
      platform: 'youtube',
      ytMode: 'source',
    };

    setIsPipelineRunning(true);
    setActiveStep(3);
    setLogs([]);
    setLogs((prev) => [
      ...prev,
      {
        id: Math.random().toString(),
        timestamp: new Date().toLocaleTimeString(),
        level: 'info',
        message: `--- [SOURCE Y-UP] BẮT ĐẦU UPLOAD VIDEO NGUỒN LÊN YOUTUBE KÈM CHAPTERS [${selectedTournament.name}] ---`,
      },
    ]);

    const started = await window.api.startPipeline(options);
    if (!started) {
      setIsPipelineRunning(false);
      setLogs((prev) => [
        ...prev,
        {
          id: Math.random().toString(),
          timestamp: new Date().toLocaleTimeString(),
          level: 'error',
          message: 'Không thể khởi động tiến trình. Vui lòng kiểm tra file video nguồn trong thư mục.',
        },
      ]);
    }
  };

  const handleKillPipeline = async () => {
    if (window.confirm('Bạn có chắc chắn muốn DỪNG KHẨN CẤP tiến trình Python đang chạy?')) {
      await window.api.killPipeline();
    }
  };

  const handleCopyLogs = () => {
    const text = logs.map((l) => `[${l.timestamp}] [${l.level.toUpperCase()}] ${l.message}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleClearLogs = () => {
    setLogs([]);
  };

  return (
    <div className="h-full flex flex-col p-3 sm:p-6 pb-24 sm:pb-6 space-y-3.5 sm:space-y-5 overflow-y-auto lg:overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 apple-card p-3 sm:p-4 shrink-0">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="cc-icon green !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Cpu className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-[var(--text-main)]">
              Pipeline Processes — Tiến Độ Tác Vụ
            </h1>
            <p className="text-xs text-[var(--text-muted)]">
              Điều khiển 4 bước tuần tự/độc lập — chỉ hiển thị thông báo quan trọng, thanh tiến độ theo thời gian thực
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {isPipelineRunning ? (
            <button
              onClick={handleKillPipeline}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#ff453a] hover:bg-[#d73a30] text-white font-bold text-xs shadow-lg shadow-[#ff453a]/30 animate-pulse transition-all cursor-pointer"
            >
              <Square className="w-4 h-4 fill-current" />
              <span>DỪNG KHẨN CẤP</span>
            </button>
          ) : (
            <>
              <button
                onClick={() => handleStartPipeline(true)}
                disabled={!selectedTournament}
                className="flex items-center gap-1.5 px-3 py-2 rounded-full bg-[#242c36] hover:bg-[#2e3743] text-[var(--text-main)] text-xs font-semibold border border-white/5 transition-all cursor-pointer"
                title="Chỉ phân tích tỷ số scoreboard bằng AI, không cắt file video"
              >
                <Terminal className="w-3.5 h-3.5 text-[var(--accent-blue)]" />
                <span>Chỉ Chạy Gemini AI</span>
              </button>

              <button
                onClick={handleStartSourceYUp}
                disabled={!selectedTournament}
                className="flex items-center gap-1.5 px-3 py-2 rounded-full bg-[#ff9f0a] hover:bg-[#e08b08] text-white text-xs font-bold shadow-[0_5px_15px_rgba(255,159,10,0.3)] transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                title="Chỉ Upload Video Nguồn (Full Match) lên YouTube kèm Chapters, bỏ qua cắt clip (--yt-mode source --skip-cut)"
              >
                <UploadCloud className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>SOURCE Y-UP</span>
              </button>

              <button
                onClick={() => handleStartPipeline()}
                disabled={!selectedTournament}
                className="btn-blue cursor-pointer"
              >
                <Play className="w-4 h-4 fill-current" />
                <span>Khởi Chạy Pipeline</span>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Main Grid: Settings Pane (Left) + Processes (Right) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-3 lg:gap-5 min-h-0">
        {/* Settings Form (4 cols) - Mobile Optimized */}
        <div className="lg:col-span-4 apple-card p-0 flex flex-col overflow-hidden lg:overflow-y-auto max-h-[60vh] lg:max-h-none">
          {/* Header - sticky */}
          <div className="sticky top-0 z-10 bg-[var(--bg-card)] px-3 sm:px-4 py-3 flex items-center justify-between border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-[#0a84ff]/15 flex items-center justify-center">
                <Sliders className="w-3.5 h-3.5 text-[#0a84ff]" />
              </div>
              <span className="text-sm font-bold text-[var(--text-main)]">Cấu Hình Tác Vụ</span>
            </div>
            <button
              onClick={() => setMobileConfigCollapsed(!mobileConfigCollapsed)}
              className="lg:hidden px-2.5 py-1 rounded-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[11px] font-semibold text-[var(--text-muted)]"
            >
              {mobileConfigCollapsed ? 'Mở' : 'Thu gọn'}
            </button>
          </div>

          <div className={`${mobileConfigCollapsed ? 'hidden lg:flex' : 'flex'} flex-col gap-4 p-3 sm:p-4 overflow-y-auto`}>
            {/* Tournament selection */}
            <div>
              <label className="block text-xs font-semibold text-[var(--text-main)] mb-1">
                Giải Đấu
              </label>
              <select
                value={selectedTournament?.path || ''}
                onChange={(e) => {
                  const found = tournaments.find((t) => t.path === e.target.value);
                  if (found) onSelectTournament(found);
                }}
                disabled={isPipelineRunning}
                className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[#0a84ff] focus:ring-2 focus:ring-[#0a84ff]/20"
              >
                {tournaments.map((t) => (
                  <option key={t.id} value={t.path}>
                    [{t.date}] {t.name}
                  </option>
                ))}
              </select>
              {selectedTournament && (
                <div className="mt-1 flex items-center gap-1.5 text-[11px] text-[var(--text-muted)]">
                  <span className={`w-2 h-2 rounded-full ${selectedTournament.hasVideo ? 'bg-[#30d158]' : 'bg-[#ff9f0a]'}`} />
                  {selectedTournament.hasVideo ? `${selectedTournament.videoSizeMb}MB • ${selectedTournament.matchCount} trận` : 'Chưa có video'}
                </div>
              )}
            </div>

            {/* YouTube Download URL */}
            <div>
              <label className="block text-xs font-semibold text-[var(--text-main)] mb-1">
                Link Video <span className="font-normal text-[var(--text-muted)]">(tùy chọn)</span>
              </label>
              <input
                type="url"
                inputMode="url"
                placeholder="https://youtube.com/watch?v=..."
                value={ytUrl}
                onChange={(e) => setYtUrl(e.target.value)}
                disabled={isPipelineRunning}
                className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[#0a84ff] focus:ring-2 focus:ring-[#0a84ff]/20"
              />
            </div>

            {/* Tên giải + Sân */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Tên Giải Đấu</label>
                <input
                  type="text"
                  value={tournamentName}
                  onChange={(e) => setTournamentName(e.target.value)}
                  disabled={isPipelineRunning}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[#0a84ff]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Sân</label>
                <input
                  type="text"
                  value={courtName}
                  onChange={(e) => setCourtName(e.target.value)}
                  disabled={isPipelineRunning}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[#0a84ff]"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Nội dung</label>
                <input
                  type="text"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={isPipelineRunning}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[#0a84ff]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Tài Trợ</label>
                <input
                  type="text"
                  placeholder="Yonex..."
                  value={sponsor}
                  onChange={(e) => setSponsor(e.target.value)}
                  disabled={isPipelineRunning}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[#0a84ff]"
                />
              </div>
            </div>

            {/* Nền tảng & Chế độ */}
            <div className="space-y-2.5">
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Nền tảng</label>
                <div className="grid grid-cols-3 gap-1.5">
                  {(['youtube','facebook','both'] as const).map(p => (
                    <button key={p} type="button" onClick={() => setPlatform(p)} disabled={isPipelineRunning}
                      className={`py-1.5 rounded-lg text-xs font-bold border transition-colors ${platform===p ? 'bg-[#0a84ff] text-white border-[#0a84ff] shadow-sm' : 'bg-[var(--bg-input)] text-[var(--text-muted)] border-[var(--border-subtle)]'}` }>
                      {p==='youtube' ? 'YouTube' : p==='facebook' ? 'Facebook' : 'Cả hai'}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Chế độ YT</label>
                <select
                  value={ytMode}
                  onChange={(e) => setYtMode(e.target.value as any)}
                  disabled={isPipelineRunning || platform === 'facebook'}
                  className="w-full px-2.5 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[#0a84ff] font-mono disabled:opacity-50"
                >
                  <option value="both">Video gốc + Clips</option>
                  <option value="clips">Chỉ Clips</option>
                  <option value="source">Chỉ Video gốc</option>
                </select>
              </div>
            </div>

            {/* 4 bước */}
            <div className="space-y-2 pt-2.5 border-t border-[var(--border-subtle)]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--text-main)] flex items-center gap-1.5">
                  <Settings2 className="w-3.5 h-3.5 text-[#0a84ff]" />
                  4 Bước
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0a84ff]/10 text-[#0a84ff] font-mono">Bỏ tick = bỏ qua</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                {[
                  {k:'dl', label:'1. Download/Import', val:!skipDownload, set:(v:boolean)=>setSkipDownload(!v), color:'#0a84ff'},
                  {k:'tl', label:'2. Timeline AI', val:!skipTimeline, set:(v:boolean)=>setSkipTimeline(!v), color:'#30d158'},
                  {k:'cut', label:'3. Cắt Clip', val:!skipCut, set:(v:boolean)=>setSkipCut(!v), color:'#ff9f0a'},
                  {k:'up', label:'4. Upload', val:!skipUpload, set:(v:boolean)=>setSkipUpload(!v), color:'#ff453a'},
                ].map(s => (
                  <label key={s.k} className={`flex items-center gap-2 px-2.5 py-1.5 rounded-lg border cursor-pointer transition-colors select-none ${s.val ? 'bg-[var(--bg-input)] border-[var(--border-subtle)]' : 'bg-[var(--bg-element)] border-transparent opacity-60'}`} style={{ borderColor: s.val ? s.color+'40' : undefined, background: s.val ? s.color+'10' : undefined }}>
                    <input type="checkbox" checked={s.val} onChange={(e) => s.set(e.target.checked)} disabled={isPipelineRunning} className="w-3.5 h-3.5 rounded accent-[#0a84ff] shrink-0" />
                    <span className="text-xs font-semibold text-[var(--text-main)] truncate">{s.label}</span>
                  </label>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                <button type="button" onClick={() => { setSkipDownload(false); setSkipTimeline(false); setSkipCut(false); setSkipUpload(false); }} disabled={isPipelineRunning} className="py-1.5 px-2 rounded-lg bg-[#0a84ff] hover:bg-[#0071e3] text-white text-xs font-bold shadow-sm transition-colors">Full Tuần Tự</button>
                <button type="button" onClick={() => { setSkipDownload(true); setSkipTimeline(true); setSkipCut(true); setSkipUpload(false); }} disabled={isPipelineRunning} className="py-1.5 px-2 rounded-lg bg-[var(--bg-input)] hover:bg-[var(--bg-highlight)] border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-main)] transition-colors">Chỉ Upload</button>
              </div>
              {/* Advanced collapsible */}
              <div className="rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] overflow-hidden">
                <button type="button" onClick={() => setShowAdvancedMobile(!showAdvancedMobile)} className="w-full flex items-center justify-between px-2.5 py-1.5 text-xs font-semibold text-[var(--text-muted)] hover:text-[var(--text-main)]">
                  <span>Nâng cao</span>
                  <span className={`transition-transform text-[10px] ${showAdvancedMobile ? 'rotate-180' : ''}`}>⌄</span>
                </button>
                {showAdvancedMobile && (
                  <div className="px-2.5 pb-2 border-t border-[var(--border-subtle)] pt-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} disabled={isPipelineRunning} className="w-3.5 h-3.5 rounded accent-[#0a84ff]" />
                      <span className="text-xs text-[var(--text-main)]">Dry-run (không đăng thật)</span>
                    </label>
                  </div>
                )}
              </div>
              <label className="hidden sm:flex items-center gap-2 cursor-pointer pt-1">
                <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} disabled={isPipelineRunning} className="w-4 h-4 rounded accent-[#0a84ff]" />
                <span className="text-xs text-[var(--text-muted)]">Dry-run</span>
              </label>
            </div>
          </div>
        </div>

        {/* Processes - Thanh tiến độ tác vụ (8 cols) */}
        <div className="lg:col-span-8 apple-card !overflow-hidden flex flex-col shadow-2xl min-h-[380px] lg:min-h-0">
          {/* Header */}
          <div className="h-10 bg-[var(--bg-dark)] border-b border-[var(--border-subtle)] flex items-center justify-between px-3 shrink-0">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-[var(--accent-blue)]" />
              <span className="text-xs font-bold text-[var(--text-main)]">Tiến Độ Tác Vụ</span>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono border ${isPipelineRunning ? 'bg-[#0a84ff]/15 text-[#0a84ff] border-[#0a84ff]/20 animate-pulse' : 'bg-[#30d158]/10 text-[#30d158] border-[#30d158]/20'}`}>
                {isPipelineRunning ? 'Đang chạy...' : logs.length === 0 ? 'Sẵn sàng' : 'Đã xong'}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <button
                onClick={handleCopyLogs}
                className="p-1 rounded-md hover:bg-[#242c36] text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors"
                title="Sao chép thông báo quan trọng"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={handleClearLogs}
                className="p-1 rounded-md hover:bg-[#242c36] text-[var(--text-muted)] hover:text-[#ff453a] transition-colors"
                title="Xóa thông báo"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Steps bar */}
          <div className="px-4 py-4 bg-[#0e1115] border-b border-[var(--border-subtle)]">
            {(() => {
              const steps = [
                { key: 'download', label: 'Download/Import', icon: Download, skip: skipDownload },
                { key: 'timeline', label: 'Timeline AI', icon: Clock, skip: skipTimeline },
                { key: 'cut', label: 'Cắt Clip', icon: Film, skip: skipCut },
                { key: 'upload', label: `Upload ${platform === 'both' ? 'YT+FB' : platform === 'facebook' ? 'Facebook' : 'YouTube'}`, icon: UploadCloud, skip: skipUpload },
              ];
              const getStatus = (idx: number, skip: boolean) => {
                if (skip) return 'skipped';
                if (!isPipelineRunning && logs.length === 0) return 'pending';
                if (logs.some(l => l.message.includes('HOÀN TẤT'))) {
                  return 'done';
                }
                if (activeStep === -2) {
                  // error: mark active as error
                  if (idx < activeStep) return 'done';
                  return idx === 0 ? 'error' : 'pending';
                }
                if (activeStep === -1) return 'done'; // finished success
                if (idx < activeStep) return 'done';
                if (idx === activeStep) return 'active';
                return 'pending';
              };
              const doneCount = steps.filter((s, i) => getStatus(i, s.skip) === 'done').length;
              const totalActive = steps.filter(s => !s.skip).length || 1;
              const progress = Math.round((doneCount / totalActive) * 100);
              return (
                <>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[11px] font-semibold text-[var(--text-muted)]">Tiến trình tổng</span>
                    <span className="text-[11px] font-mono font-bold text-[var(--accent-blue)]">{isPipelineRunning ? `${progress}%` : doneCount === totalActive && logs.length > 0 ? '100%' : '—'}</span>
                  </div>
                  <div className="h-1.5 w-full bg-[var(--bg-input)] rounded-full overflow-hidden mb-4">
                    <div className="h-full bg-[#0a84ff] transition-all duration-500" style={{ width: `${isPipelineRunning ? Math.max(10, progress) : progress}%` }} />
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    {steps.map((step, idx) => {
                      const status = getStatus(idx, step.skip);
                      const Icon = step.icon;
                      return (
                        <div key={step.key} className={`relative flex flex-col items-center gap-1.5 p-2.5 rounded-xl border text-center transition-all ${
                          status === 'active' ? 'bg-[#0a84ff]/10 border-[#0a84ff]/30 shadow-sm' :
                          status === 'done' ? 'bg-[#30d158]/10 border-[#30d158]/25' :
                          status === 'skipped' ? 'bg-[var(--bg-input)] border-[var(--border-subtle)] opacity-50' :
                          status === 'error' ? 'bg-[#ff453a]/10 border-[#ff453a]/30' :
                          'bg-[var(--bg-input)] border-[var(--border-subtle)]'
                        }`}>
                          <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                            status === 'active' ? 'bg-[#0a84ff] text-white animate-pulse' :
                            status === 'done' ? 'bg-[#30d158] text-white' :
                            status === 'skipped' ? 'bg-[var(--bg-element)] text-[var(--text-faint)]' :
                            status === 'error' ? 'bg-[#ff453a] text-white' :
                            'bg-[var(--bg-element)] text-[var(--text-muted)]'
                          }`}>
                            {status === 'active' ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> :
                             status === 'done' ? <Check className="w-3.5 h-3.5" /> :
                             status === 'skipped' ? <Minus className="w-3.5 h-3.5" /> :
                             status === 'error' ? <X className="w-3.5 h-3.5" /> :
                             <span className="text-[11px]">{idx + 1}</span>}
                          </div>
                          <Icon className={`w-3.5 h-3.5 ${status === 'active' ? 'text-[#0a84ff]' : status === 'done' ? 'text-[#30d158]' : 'text-[var(--text-muted)]'}`} />
                          <span className={`text-[11px] font-semibold leading-tight ${status === 'active' ? 'text-[#0a84ff]' : status === 'done' ? 'text-[#30d158]' : status === 'skipped' ? 'text-[var(--text-faint)] line-through' : 'text-[var(--text-muted)]'}`}>{step.label}</span>
                          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${status === 'active' ? 'bg-[#0a84ff]/15 text-[#0a84ff]' : status === 'done' ? 'bg-[#30d158]/15 text-[#30d158]' : status === 'skipped' ? 'bg-[var(--bg-element)] text-[var(--text-faint)]' : 'bg-transparent text-[var(--text-faint)]'}`}>
                            {status === 'active' ? 'Đang chạy' : status === 'done' ? 'Hoàn tất' : status === 'skipped' ? 'Bỏ qua' : status === 'error' ? 'Lỗi' : 'Chờ'}
                          </span>
                          {idx < 3 && (
                            <div className={`hidden sm:block absolute top-5 -right-1 w-2 h-0.5 ${(() => {
                              const nextStatus = getStatus(idx+1, steps[idx+1].skip);
                              const curDone = status === 'done';
                              return curDone ? 'bg-[#30d158]/50' : 'bg-[var(--border-subtle)]';
                            })()}`} />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </>
              );
            })()}
          </div>

          {/* Chỉ thông báo quan trọng */}
          <div
            ref={logContainerRef}
            className="flex-1 p-3 bg-[#0e1115] overflow-y-auto space-y-2 min-h-[140px]"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-[var(--accent-blue)]" />
                Thông báo quan trọng
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
                {logs.filter(isImportant).length} tin
              </span>
            </div>
            {(() => {
              const important = logs.filter(isImportant);
              if (important.length === 0) {
                return (
                  <div className="py-8 text-center text-slate-400 text-xs space-y-2">
                    <Terminal className="w-6 h-6 mx-auto opacity-20" />
                    <p>{isPipelineRunning ? 'Đang xử lý, thông báo quan trọng sẽ hiện ở đây...' : 'Chưa có thông báo quan trọng. Nhấn Khởi Chạy để bắt đầu.'}</p>
                    <p className="text-[11px] text-slate-500">Hệ thống chỉ hiển thị lỗi, hoàn tất, cảnh báo và mốc bước chính — ẩn log nhiễu chi tiết.</p>
                  </div>
                );
              }
              return important.slice(-30).map((log) => {
                const isErr = log.level === 'error';
                const isOk = log.level === 'success';
                const isWarn = log.level === 'warn';
                return (
                  <div key={log.id} className={`flex items-start gap-2 px-2.5 py-2 rounded-lg border text-xs leading-relaxed ${
                    isErr ? 'bg-[#ff453a]/10 border-[#ff453a]/20 text-[#ff9f9f]' :
                    isOk ? 'bg-[#30d158]/10 border-[#30d158]/20 text-[#b6f0c5]' :
                    isWarn ? 'bg-[#ff9f0a]/10 border-[#ff9f0a]/20 text-[#ffd8a8]' :
                    'bg-[var(--bg-input)] border-[var(--border-subtle)] text-slate-200'
                  }`}>
                    <span className="shrink-0 mt-0.5">
                      {isErr ? <X className="w-3.5 h-3.5 text-[#ff453a]" /> :
                       isOk ? <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158]" /> :
                       isWarn ? <AlertCircle className="w-3.5 h-3.5 text-[#ff9f0a]" /> :
                       <Info className="w-3.5 h-3.5 text-[#0a84ff]" />}
                    </span>
                    <span className="text-[10px] font-mono opacity-60 shrink-0">{log.timestamp}</span>
                    <span className="flex-1 break-words font-medium">{log.message.replace(/^[\-=─\s]+/, '')}</span>
                  </div>
                );
              });
            })()}
          </div>
        </div>
      </div>
    </div>
  );
};
