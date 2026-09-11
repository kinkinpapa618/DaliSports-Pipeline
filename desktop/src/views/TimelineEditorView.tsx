import React, { useState, useEffect } from 'react';
import { 
  Clock, Save, Plus, Trash2, CheckCircle, AlertTriangle, 
  Play, RefreshCw, Trophy, CheckSquare, Square, Flame, Filter 
} from 'lucide-react';
import { MatchTimelineItem, TournamentInfo } from '../types';

interface TimelineEditorViewProps {
  tournaments: TournamentInfo[];
  selectedTournament: TournamentInfo | null;
  onSelectTournament: (t: TournamentInfo) => void;
  onNavigateToPipeline: (t: TournamentInfo) => void;
}

export const TimelineEditorView: React.FC<TimelineEditorViewProps> = ({
  tournaments,
  selectedTournament,
  onSelectTournament,
  onNavigateToPipeline,
}) => {
  const [matches, setMatches] = useState<MatchTimelineItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [sourceFile, setSourceFile] = useState<string | null>(null);

  // Load timeline when selectedTournament changes
  useEffect(() => {
    if (selectedTournament) {
      loadTimeline(selectedTournament.path);
    } else if (tournaments.length > 0) {
      onSelectTournament(tournaments[0]);
    }
  }, [selectedTournament]);

  const loadTimeline = async (path: string) => {
    setLoading(true);
    setSaveSuccess(false);
    try {
      const res = await window.api.getTimeline(path);
      setSourceFile(res.detectedFile || (selectedTournament?.timelineFile || null));
      const items = (res.matches || []).map((m) => ({
        ...m,
        selected: m.selected !== false,
      }));
      setMatches(items);
      setDirty(false);
    } catch (err) {
      console.error('Lỗi tải timeline:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleMatchChange = (index: number, field: keyof MatchTimelineItem, value: any) => {
    const updated = [...matches];
    updated[index] = { ...updated[index], [field]: value };
    setMatches(updated);
    setDirty(true);
    setSaveSuccess(false);
  };

  const handleScoreChange = (index: number, setKey: 'set1' | 'set2' | 'set3', value: string) => {
    const updated = [...matches];
    const currentScores = updated[index].scores || {};
    updated[index] = {
      ...updated[index],
      scores: {
        ...currentScores,
        [setKey]: value,
      },
    };
    setMatches(updated);
    setDirty(true);
    setSaveSuccess(false);
  };

  // Toggle individual match selection for cutting
  const handleToggleSelect = (index: number) => {
    const updated = [...matches];
    updated[index] = { 
      ...updated[index], 
      selected: !(updated[index].selected !== false) 
    };
    setMatches(updated);
    setDirty(true);
    setSaveSuccess(false);
  };

  // Shortcut 1: Cắt toàn bộ
  const handleSelectAll = () => {
    const updated = matches.map((m) => ({ ...m, selected: true }));
    setMatches(updated);
    setDirty(true);
    setSaveSuccess(false);
  };

  // Shortcut 2: Cắt bán kết - chung kết
  const handleSelectSemiAndFinal = () => {
    const regex = /bán kết|chung kết|bk|ck|semi|final|vck/i;
    const updated = matches.map((m) => {
      const isTarget = regex.test(m.round || '') || 
                       regex.test(m.category || '') || 
                       regex.test(m.court || '');
      return { ...m, selected: isTarget };
    });
    setMatches(updated);
    setDirty(true);
    setSaveSuccess(false);
  };

  // Shortcut 3: Không cắt
  const handleDeselectAll = () => {
    const updated = matches.map((m) => ({ ...m, selected: false }));
    setMatches(updated);
    setDirty(true);
    setSaveSuccess(false);
  };

  const handleAddMatch = () => {
    const newId = matches.length + 1;
    const newMatch: MatchTimelineItem = {
      match_id: newId,
      court: 'Sân 1',
      round: 'Vòng Bảng',
      category: 'Đôi Nam',
      player_a: 'Cặp VĐV 1',
      player_b: 'Cặp VĐV 2',
      start_time: '00:00:00',
      end_time: '00:20:00',
      scores: { set1: '21-19', set2: '21-18' },
      selected: true,
    };
    setMatches([...matches, newMatch]);
    setDirty(true);
  };

  const handleDeleteMatch = (index: number) => {
    if (window.confirm(`Xác nhận xóa Trận #${matches[index].match_id || index + 1}?`)) {
      const updated = matches.filter((_, i) => i !== index);
      setMatches(updated);
      setDirty(true);
    }
  };

  const handleSaveTimeline = async () => {
    if (!selectedTournament) return;
    try {
      const ok = await window.api.saveTimeline(selectedTournament.path, matches);
      if (ok) {
        setSaveSuccess(true);
        setDirty(false);
        setTimeout(() => setSaveSuccess(false), 3500);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Helper duration parse
  const parseSeconds = (t: string | number): number => {
    if (typeof t === 'number') return t;
    const parts = t.split(':').map(Number);
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return 0;
  };

  const formatDuration = (start: string | number, end: string | number): string => {
    const s1 = parseSeconds(start);
    const s2 = parseSeconds(end);
    const diff = Math.max(0, s2 - s1);
    const m = Math.floor(diff / 60);
    const s = diff % 60;
    return `${m}m ${s}s`;
  };

  // Stats for selected matches
  const selectedMatches = matches.filter((m) => m.selected !== false);
  const selectedCount = selectedMatches.length;
  const selectedTotalSeconds = selectedMatches.reduce(
    (acc, m) => acc + Math.max(0, parseSeconds(m.end_time) - parseSeconds(m.start_time)),
    0
  );
  const selectedTotalMinutes = Math.round(selectedTotalSeconds / 60);

  const handleStartCutSelected = async () => {
    if (!selectedTournament) return;
    // Auto-save before navigating
    await window.api.saveTimeline(selectedTournament.path, matches);
    onNavigateToPipeline(selectedTournament);
  };

  return (
    <div className="h-full flex flex-col p-3 sm:p-6 pb-24 sm:pb-6 space-y-3.5 sm:space-y-5 overflow-y-auto">
      {/* Top Header & Tournament Selector */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3 sm:gap-4 apple-card p-3 sm:p-4">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="cc-icon blue !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Clock className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-[var(--text-main)]">Hiệu Đính Scoreboard & Mốc Timeline</h1>
            <p className="text-xs text-[var(--text-muted)]">
              Kiểm tra tỷ số, căn chỉnh mốc thời gian và chọn các trận đấu cụ thể để xuất video clip highlight
            </p>
          </div>
        </div>

        {/* Tournament Dropdown & Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={selectedTournament?.path || ''}
            onChange={(e) => {
              const found = tournaments.find((t) => t.path === e.target.value);
              if (found) onSelectTournament(found);
            }}
            className="w-full sm:w-auto px-3.5 py-2 rounded-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-medium focus:outline-none focus:border-[var(--accent-blue)] shadow-sm"
          >
            {tournaments.map((t) => (
              <option key={t.id} value={t.path}>
                [{t.date}] {t.name} ({t.matchCount} trận)
              </option>
            ))}
          </select>

          <button
            onClick={() => selectedTournament && loadTimeline(selectedTournament.path)}
            className="circle-btn !w-8 !h-8 text-xs"
            title="Tải lại từ tệp gốc"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={handleAddMatch}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-full bg-[#242c36] hover:bg-[#2e3743] text-[var(--text-main)] text-xs font-semibold border border-white/5 transition-all shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Thêm Trận</span>
          </button>

          <button
            onClick={handleSaveTimeline}
            disabled={!dirty && !saveSuccess}
            className={`btn-blue !py-2 !px-4 text-xs font-bold transition-all cursor-pointer ${
              saveSuccess
                ? '!bg-[#30d158] text-slate-950 !shadow-[0_5px_15px_rgba(48,209,88,0.35)]'
                : dirty
                ? ''
                : '!bg-[#242c36] !text-[var(--text-faint)] cursor-not-allowed !shadow-none'
            }`}
          >
            {saveSuccess ? (
              <>
                <CheckCircle className="w-3.5 h-3.5" />
                <span>Đã Lưu Backup (.bak)</span>
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                <span>Lưu Timeline {dirty ? '*' : ''}</span>
              </>
            )}
          </button>

          {selectedTournament && (
            <button
              onClick={handleStartCutSelected}
              className="flex items-center gap-1.5 px-4 py-2 rounded-full bg-[#0a84ff] hover:bg-[#0071e3] text-white text-xs font-bold transition-all shadow-md shadow-[#0a84ff]/25 cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>Cắt Highlights ({selectedCount} trận đã chọn)</span>
            </button>
          )}
        </div>
      </div>

      {/* 3 Shortcut Buttons Row */}
      {matches.length > 0 && (
        <div className="apple-card !p-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Shortcuts */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5 mr-1">
              <Filter className="w-3.5 h-3.5 text-[var(--accent-blue)]" />
              <span>Chọn nhanh trận cắt:</span>
            </span>

            {/* Shortcut 1: Cắt Toàn Bộ */}
            <button
              type="button"
              onClick={handleSelectAll}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border cursor-pointer ${
                selectedCount === matches.length
                  ? 'bg-[#0a84ff]/15 text-[#0a84ff] border-[#0a84ff]/30 shadow-sm'
                  : 'bg-[var(--bg-input)] text-[var(--text-muted)] border-[var(--border-subtle)] hover:text-[var(--text-main)]'
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5 text-[#0a84ff]" />
              <span>Cắt Toàn Bộ ({matches.length})</span>
            </button>

            {/* Shortcut 2: Cắt Bán Kết - Chung Kết */}
            <button
              type="button"
              onClick={handleSelectSemiAndFinal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border bg-[#ff9f0a]/15 text-[#ff9f0a] border-[#ff9f0a]/30 hover:bg-[#ff9f0a]/25 cursor-pointer"
              title="Chỉ chọn những trận có vòng thi đấu là Bán Kết, Chung Kết, BK, CK, Semi, Final"
            >
              <Trophy className="w-3.5 h-3.5 text-[#ff9f0a]" />
              <span>Cắt Bán Kết - Chung Kết</span>
            </button>

            {/* Shortcut 3: Không Cắt */}
            <button
              type="button"
              onClick={handleDeselectAll}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border cursor-pointer ${
                selectedCount === 0
                  ? 'bg-[#242c36] text-[var(--text-main)] border-white/10'
                  : 'bg-[var(--bg-input)] text-[var(--text-muted)] border-[var(--border-subtle)] hover:text-[var(--text-main)]'
              }`}
            >
              <Square className="w-3.5 h-3.5" />
              <span>Không Cắt (0)</span>
            </button>
          </div>

          {/* Selection counter & duration */}
          <div className="flex items-center gap-2.5 text-xs font-mono">
            {sourceFile && (
              <span className="px-2.5 py-1 rounded-md bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--accent-blue)] font-medium truncate max-w-[220px]" title={`Tệp timeline nguồn: ${sourceFile}`}>
                📁 {sourceFile}
              </span>
            )}
            <span className="px-2.5 py-1 rounded-md bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
              Đã chọn: <strong className="text-[var(--accent-blue)] font-bold">{selectedCount}</strong> / {matches.length} trận
            </span>
            <span className="px-2.5 py-1 rounded-md bg-[var(--bg-input)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
              Thời lượng xuất: <strong className="text-[var(--accent-orange)] font-bold">~{selectedTotalMinutes} phút</strong>
            </span>
          </div>
        </div>
      )}

      {/* Matches List */}
      {loading ? (
        <div className="text-center py-20 text-slate-400">
          <Clock className="w-8 h-8 animate-spin mx-auto mb-2 text-blue-400" />
          <p className="text-xs">Đang đọc timeline.json...</p>
        </div>
      ) : matches.length === 0 ? (
        <div className="text-center py-20 bg-slate-900/30 rounded-2xl border border-slate-800 border-dashed p-8">
          <AlertTriangle className="w-10 h-10 mx-auto mb-3 text-amber-400/60" />
          <h3 className="text-sm font-bold text-slate-200">Chưa có timeline trận đấu</h3>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            Giải đấu này chưa có file timeline.json hoặc Gemini AI chưa phân tích scoreboard. 
            Bạn có thể khởi chạy AI bóc tách tự động hoặc nhấn "Thêm Trận" để nhập thủ công.
          </p>
          <div className="flex items-center justify-center gap-3 mt-4">
            <button
              onClick={handleAddMatch}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white"
            >
              Nhập Thủ Công
            </button>
            {selectedTournament && (
              <button
                onClick={() => onNavigateToPipeline(selectedTournament)}
                className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-xs font-bold text-slate-950"
              >
                Chạy Gemini AI Quét Tự Động
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3">
            {matches.map((match, idx) => {
              const isSelected = match.selected !== false;

              return (
                <div
                  key={idx}
                  className={`apple-card p-4 space-y-3 transition-all ${
                    isSelected
                      ? 'border-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.35)]'
                      : 'opacity-50 grayscale'
                  }`}
                >
                  {/* Match Card Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-[var(--border-subtle)]">
                    <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
                      {/* Checkbox chọn cắt trận */}
                      <label 
                        className="flex items-center gap-1.5 sm:gap-2 cursor-pointer select-none px-2.5 py-1 rounded-full bg-[var(--bg-input)] border border-[var(--border-subtle)] hover:border-white/20 transition-colors"
                        title="Tick chọn để xuất video trận này"
                      >
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleSelect(idx)}
                          className="w-4 h-4 rounded bg-[var(--bg-element)] border-[var(--border-subtle)] text-[#0a84ff] focus:ring-0 cursor-pointer accent-[#0a84ff]"
                        />
                        <span className={`text-[10px] sm:text-[11px] font-bold ${isSelected ? 'text-[var(--accent-blue)]' : 'text-[var(--text-muted)]'}`}>
                          {isSelected ? 'CẮT TRẬN' : 'BỎ QUA'}
                        </span>
                      </label>

                      <span className="w-6 h-6 rounded-full bg-[#242c36] text-[var(--accent-blue)] font-mono font-bold text-xs flex items-center justify-center">
                        #{idx + 1}
                      </span>
                      <input
                        type="text"
                        value={match.round || 'Vòng Bảng'}
                        onChange={(e) => handleMatchChange(idx, 'round', e.target.value)}
                        placeholder="Vòng"
                        className="px-2 py-1 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-main)] w-20 sm:w-28 focus:outline-none focus:border-[var(--accent-blue)]"
                      />
                      <input
                        type="text"
                        value={match.category || 'Đôi Nam'}
                        onChange={(e) => handleMatchChange(idx, 'category', e.target.value)}
                        placeholder="Nội dung"
                        className="px-2 py-1 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-main)] w-20 sm:w-24 focus:outline-none focus:border-[var(--accent-blue)]"
                      />
                      <input
                        type="text"
                        value={match.court || 'Sân 1'}
                        onChange={(e) => handleMatchChange(idx, 'court', e.target.value)}
                        placeholder="Sân"
                        className="px-2 py-1 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] w-16 sm:w-20 focus:outline-none focus:border-[var(--accent-blue)]"
                      />
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] sm:text-[11px] px-2 py-0.5 rounded-full bg-[#0a84ff]/15 border border-[#0a84ff]/20 text-[#0a84ff] font-mono font-medium">
                        {formatDuration(match.start_time, match.end_time)}
                      </span>

                      <button
                        onClick={() => handleDeleteMatch(idx)}
                        className="circle-btn !w-7 !h-7 text-xs hover:!text-[#ff453a]"
                        title="Xóa trận này"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Match Competitors & Scores */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
                    {/* Players / Teams */}
                    <div className="space-y-1.5 md:col-span-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-[var(--text-muted)] w-12">ĐỘI A:</span>
                        <input
                          type="text"
                          value={match.player_a || ''}
                          onChange={(e) => handleMatchChange(idx, 'player_a', e.target.value)}
                          placeholder="Tên vận động viên Đội A"
                          className="flex-1 px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
                        />
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold text-[var(--text-muted)] w-12">ĐỘI B:</span>
                        <input
                          type="text"
                          value={match.player_b || ''}
                          onChange={(e) => handleMatchChange(idx, 'player_b', e.target.value)}
                          placeholder="Tên vận động viên Đội B"
                          className="flex-1 px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
                        />
                      </div>
                    </div>

                    {/* Set Scores */}
                    <div className="bg-[var(--bg-input)] p-2.5 rounded-xl border border-[var(--border-subtle)] space-y-1">
                      <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
                        Tỷ số các set:
                      </div>
                      <div className="grid grid-cols-3 gap-1.5">
                        <input
                          type="text"
                          placeholder="Set 1"
                          value={match.scores?.set1 || ''}
                          onChange={(e) => handleScoreChange(idx, 'set1', e.target.value)}
                          className="px-2 py-1 rounded bg-[var(--bg-element)] border border-white/5 text-xs text-center font-mono text-[var(--accent-blue)] focus:outline-none font-bold"
                        />
                        <input
                          type="text"
                          placeholder="Set 2"
                          value={match.scores?.set2 || ''}
                          onChange={(e) => handleScoreChange(idx, 'set2', e.target.value)}
                          className="px-2 py-1 rounded bg-[var(--bg-element)] border border-white/5 text-xs text-center font-mono text-[var(--accent-blue)] focus:outline-none font-bold"
                        />
                        <input
                          type="text"
                          placeholder="Set 3"
                          value={match.scores?.set3 || ''}
                          onChange={(e) => handleScoreChange(idx, 'set3', e.target.value)}
                          className="px-2 py-1 rounded bg-[var(--bg-element)] border border-white/5 text-xs text-center font-mono text-[var(--accent-blue)] focus:outline-none font-bold"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Timestamps Row */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs border-t border-[var(--border-subtle)] bg-[var(--bg-input)] p-2.5 rounded-xl">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <span className="text-[var(--text-muted)] font-medium">Bắt đầu:</span>
                        <input
                          type="text"
                          value={match.start_time}
                          onChange={(e) => handleMatchChange(idx, 'start_time', e.target.value)}
                          placeholder="00:00:00"
                          className="w-24 px-2 py-1 rounded bg-[var(--bg-element)] border border-white/5 font-mono text-[var(--accent-green)] text-xs text-center focus:outline-none focus:border-[var(--accent-blue)]"
                        />
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-[var(--text-muted)] font-medium">Kết thúc:</span>
                        <input
                          type="text"
                          value={match.end_time}
                          onChange={(e) => handleMatchChange(idx, 'end_time', e.target.value)}
                          placeholder="00:00:00"
                          className="w-24 px-2 py-1 rounded bg-[var(--bg-element)] border border-white/5 font-mono text-[var(--accent-green)] text-xs text-center focus:outline-none focus:border-[var(--accent-blue)]"
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[var(--text-muted)] text-[11px]">Đội thắng:</span>
                      <input
                        type="text"
                        value={match.winner || ''}
                        onChange={(e) => handleMatchChange(idx, 'winner', e.target.value)}
                        placeholder="Đội A hoặc Đội B"
                        className="px-2 py-1 rounded bg-[var(--bg-element)] border border-white/5 text-xs text-[var(--text-main)] focus:outline-none"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
