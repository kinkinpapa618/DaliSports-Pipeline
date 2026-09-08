import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, Square, Terminal, Copy, Trash2, CheckCircle2, 
  AlertCircle, Settings2, Sliders, ShieldAlert, Cpu, UploadCloud 
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

  // Form options
  const [ytUrl, setYtUrl] = useState('');
  const [courtName, setCourtName] = useState('Sân 1');
  const [tournamentName, setTournamentName] = useState('');
  const [sponsor, setSponsor] = useState('');
  const [category, setCategory] = useState('Đôi Nam');
  const [skipCut, setSkipCut] = useState(false);
  const [dryRun, setDryRun] = useState(false);
  const [ytMode, setYtMode] = useState<'both' | 'source' | 'clips'>('both');

  const logContainerRef = useRef<HTMLDivElement>(null);

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

  // Subscribe to logs and exit event safely
  useEffect(() => {
    if (window.api && typeof window.api.onPipelineLog === 'function') {
      window.api.onPipelineLog((log) => {
        if (log) {
          setLogs((prev) => [...prev, log]);
        }
      });
    }

    if (window.api && typeof window.api.onPipelineExit === 'function') {
      window.api.onPipelineExit((code) => {
        setIsPipelineRunning(false);
      });
    }
  }, []);

  // Auto scroll
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const handleStartPipeline = async (forceSkipCut?: boolean) => {
    if (!selectedTournament) return;

    const options: PipelineOptions = {
      tournamentPath: selectedTournament.path,
      ytUrl: ytUrl.trim() || undefined,
      courtName: courtName.trim() || undefined,
      tournamentName: tournamentName.trim() || undefined,
      sponsor: sponsor.trim() || undefined,
      category: category.trim() || undefined,
      skipCut: forceSkipCut !== undefined ? forceSkipCut : skipCut,
      dryRun,
      ytMode,
    };

    setIsPipelineRunning(true);
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
      skipCut: true,
      dryRun,
      ytMode: 'source',
    };

    setIsPipelineRunning(true);
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
    <div className="h-full flex flex-col p-3 sm:p-6 space-y-3.5 sm:space-y-5 overflow-y-auto lg:overflow-hidden">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 apple-card p-3 sm:p-4 shrink-0">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="cc-icon green !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Cpu className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-[var(--text-main)]">
              Pipeline Trực Tiếp & Console Logs
            </h1>
            <p className="text-xs text-[var(--text-muted)]">
              Điều khiển tự động hóa toàn bộ luồng: Tải Video → Gemini AI Timeline → FFmpeg Cut → Upload FB/YT
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

      {/* Main Grid: Settings Pane (Left) + Console Output (Right) */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-5 min-h-0">
        {/* Settings Form (4 cols) */}
        <div className="lg:col-span-4 apple-card p-3.5 sm:p-4 flex flex-col space-y-4 overflow-y-auto">
          <div className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider flex items-center gap-2 pb-2 border-b border-[var(--border-subtle)]">
            <Sliders className="w-4 h-4 text-[var(--accent-blue)]" />
            <span>Cấu Hình Tác Vụ</span>
          </div>

          {/* Tournament selection */}
          <div>
            <label className="block text-[11px] font-semibold text-slate-400 mb-1">
              Thư mục Giải Đấu:
            </label>
            <select
              value={selectedTournament?.path || ''}
              onChange={(e) => {
                const found = tournaments.find((t) => t.path === e.target.value);
                if (found) onSelectTournament(found);
              }}
              disabled={isPipelineRunning}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
            >
              {tournaments.map((t) => (
                <option key={t.id} value={t.path}>
                  [{t.date}] {t.name}
                </option>
              ))}
            </select>
          </div>

          {/* YouTube Download URL */}
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">
              YouTube Video URL (Tùy chọn tải về):
            </label>
            <input
              type="text"
              placeholder="https://www.youtube.com/watch?v=..."
              value={ytUrl}
              onChange={(e) => setYtUrl(e.target.value)}
              disabled={isPipelineRunning}
              className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[var(--accent-blue)]"
            />
          </div>

          {/* Tournament Name & Sponsor */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">
                Tên Giải Đấu:
              </label>
              <input
                type="text"
                value={tournamentName}
                onChange={(e) => setTournamentName(e.target.value)}
                disabled={isPipelineRunning}
                className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">
                Sân thi đấu:
              </label>
              <input
                type="text"
                value={courtName}
                onChange={(e) => setCourtName(e.target.value)}
                disabled={isPipelineRunning}
                className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">
                Nội dung:
              </label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={isPipelineRunning}
                className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">
                Nhà Tài Trợ:
              </label>
              <input
                type="text"
                placeholder="VD: Li-Ning, Yonex..."
                value={sponsor}
                onChange={(e) => setSponsor(e.target.value)}
                disabled={isPipelineRunning}
                className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
          </div>

          {/* YouTube Upload Mode */}
          <div>
            <label className="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">
              Chế độ Upload YouTube (--yt-mode):
            </label>
            <select
              value={ytMode}
              onChange={(e) => setYtMode(e.target.value as any)}
              disabled={isPipelineRunning}
              className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)] font-mono"
            >
              <option value="both">both (Video Gốc + Các Clips Đã Cắt)</option>
              <option value="clips">clips (Chỉ Upload Các Clips Đã Cắt)</option>
              <option value="source">source (Chỉ Upload Video Nguồn Full)</option>
            </select>
          </div>

          {/* Toggles */}
          <div className="space-y-2 pt-2 border-t border-[var(--border-subtle)]">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={skipCut}
                onChange={(e) => setSkipCut(e.target.checked)}
                disabled={isPipelineRunning}
                className="w-4 h-4 rounded bg-[var(--bg-input)] border-[var(--border-subtle)] text-[var(--accent-blue)] focus:ring-0 accent-[var(--accent-blue)] cursor-pointer"
              />
              <span className="text-xs text-[var(--text-main)]">
                --skip-cut (Bỏ qua bước cắt FFmpeg, chỉ xuất timeline)
              </span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
                disabled={isPipelineRunning}
                className="w-4 h-4 rounded bg-[var(--bg-input)] border-[var(--border-subtle)] text-[var(--accent-blue)] focus:ring-0 accent-[var(--accent-blue)] cursor-pointer"
              />
              <span className="text-xs text-[var(--text-main)]">
                --dry-run (Chế độ mô phỏng kiểm tra, không upload/cắt)
              </span>
            </label>
          </div>
        </div>

        {/* Live Terminal Console (8 cols) */}
        <div className="lg:col-span-8 apple-card !overflow-hidden flex flex-col shadow-2xl min-h-[380px] lg:min-h-0">
          {/* Console Header Bar */}
          <div className="h-10 bg-[var(--bg-dark)] border-b border-[var(--border-subtle)] flex items-center justify-between px-3 shrink-0">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[var(--accent-blue)]" />
              <span className="text-xs font-mono font-bold text-[var(--text-main)]">
                Terminal Output Console
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#242c36] text-[var(--text-muted)] font-mono border border-white/5">
                {logs.length} dòng
              </span>
            </div>

            <div className="flex items-center gap-2">
              <label className="flex items-center gap-1.5 text-[11px] text-[var(--text-muted)] cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={autoScroll}
                  onChange={(e) => setAutoScroll(e.target.checked)}
                  className="rounded bg-[var(--bg-input)] border-[var(--border-subtle)] text-[var(--accent-blue)] accent-[var(--accent-blue)]"
                />
                <span>Tự Cuộn</span>
              </label>

              <button
                onClick={handleCopyLogs}
                className="p-1 rounded-md hover:bg-[#242c36] text-[var(--text-muted)] hover:text-[var(--text-main)] transition-colors cursor-pointer"
                title="Sao chép toàn bộ logs"
              >
                <Copy className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={handleClearLogs}
                className="p-1 rounded-md hover:bg-[#242c36] text-[var(--text-muted)] hover:text-[#ff453a] transition-colors cursor-pointer"
                title="Xóa màn hình console"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* Console Logs Body */}
          <div
            ref={logContainerRef}
            className="flex-1 p-4 bg-[#0e1115] font-['JetBrains_Mono',monospace] text-[12px] leading-relaxed overflow-y-auto space-y-1 select-text"
          >
            {logs.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-400 text-xs">
                <div className="text-center space-y-2">
                  <Terminal className="w-8 h-8 mx-auto opacity-30" />
                  <p>Console sẵn sàng. Nhấn "Khởi Chạy Full Pipeline" để bắt đầu xử lý.</p>
                </div>
              </div>
            ) : (
              logs.map((log) => {
                let badgeColor = 'text-slate-400';
                if (log.level === 'error') badgeColor = 'text-red-400 bg-red-500/10';
                else if (log.level === 'success') badgeColor = 'text-emerald-400 bg-emerald-500/10';
                else if (log.level === 'warn') badgeColor = 'text-amber-400 bg-amber-500/10';

                return (
                  <div key={log.id} className="flex items-start gap-2.5 group">
                    <span className="text-slate-400 text-[10px] shrink-0 font-mono mt-0.5">
                      {log.timestamp}
                    </span>
                    <span
                      className={`text-[10px] uppercase font-bold px-1 rounded shrink-0 ${badgeColor}`}
                    >
                      {log.level}
                    </span>
                    <span
                      className={`break-all ${
                        log.level === 'error'
                          ? 'text-red-300 font-semibold'
                          : log.level === 'success'
                          ? 'text-emerald-300 font-semibold'
                          : log.level === 'warn'
                          ? 'text-amber-300'
                          : 'text-slate-200'
                      }`}
                    >
                      {log.message}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
