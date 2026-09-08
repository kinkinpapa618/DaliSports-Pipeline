import React, { useState, useEffect } from 'react';
import { 
  Share2, Copy, Check, Video, Globe,
  Sparkles, Tag, FileText, CheckCircle2, ShieldCheck, Key, Trophy 
} from 'lucide-react';
import { SeoPreviewResult, TournamentInfo } from '../types';

interface SeoPreviewViewProps {
  tournaments: TournamentInfo[];
  selectedTournament: TournamentInfo | null;
}

const DEFAULT_SEO: SeoPreviewResult = {
  title: '',
  description: '',
  tags: [],
};

export const SeoPreviewView: React.FC<SeoPreviewViewProps> = ({
  tournaments,
  selectedTournament,
}) => {
  const [activeTournament, setActiveTournament] = useState<TournamentInfo | null>(selectedTournament);
  const [tournamentName, setTournamentName] = useState('');
  const [sport, setSport] = useState('CauLong');
  const [round, setRound] = useState('Chung Kết');
  const [category, setCategory] = useState('Đôi Nam');
  const [playerA, setPlayerA] = useState('Nguyễn Văn A / Trần Văn B');
  const [playerB, setPlayerB] = useState('Lê Văn C / Phạm Văn D');
  const [court, setCourt] = useState('Sân 1');
  const [sponsor, setSponsor] = useState('Li-Ning');
  const [score, setScore] = useState('21-19, 18-21, 21-17');

  const [seoResult, setSeoResult] = useState<SeoPreviewResult>(DEFAULT_SEO);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Sync selected tournament
  useEffect(() => {
    if (selectedTournament) {
      setActiveTournament(selectedTournament);
      setTournamentName(selectedTournament.name);
      setSport(selectedTournament.sportType === 'pickleball' ? 'Pickleball' : 'CauLong');
    } else if (tournaments.length > 0 && !activeTournament) {
      setActiveTournament(tournaments[0]);
      setTournamentName(tournaments[0].name);
      setSport(tournaments[0].sportType === 'pickleball' ? 'Pickleball' : 'CauLong');
    }
  }, [selectedTournament, tournaments]);

  // Recalculate SEO preview with error handling
  useEffect(() => {
    const fetchPreview = async () => {
      try {
        if (window.api && typeof window.api.getSeoPreview === 'function') {
          const res = await window.api.getSeoPreview({
            tournamentName: tournamentName || 'GIẢI ĐẤU DALI SPORTS',
            sport,
            round,
            category,
            playerA,
            playerB,
            court,
            sponsor,
            score,
          });
          if (res && res.title) {
            setSeoResult(res);
            return;
          }
        }
      } catch (err) {
        console.error('Lỗi khi gọi API SEO preview:', err);
      }

      // Local fallback in case IPC is delayed
      const tName = tournamentName || 'GIẢI ĐẤU THỂ THAO 2026';
      setSeoResult({
        title: `[${round.toUpperCase()}] ${playerA} vs ${playerB} | ${category} - ${tName}`,
        description: `🏸 TRỰC TIẾP & HIGHLIGHTS: ${tName}\n🏆 Trận: ${playerA} VS ${playerB}\n📌 Vòng: ${round} | Nội dung: ${category} - ${court}\n${score ? `Tỷ số: ${score}\n` : ''}${sponsor ? `✨ Nhà tài trợ: ${sponsor}\n` : ''}🔥 Theo dõi DaliSports để xem trọn bộ clips hấp dẫn nhất!`,
        tags: ['DaliSports', sport, category, round, playerA, playerB, tName],
      });
    };

    fetchPreview();
  }, [tournamentName, sport, round, category, playerA, playerB, court, sponsor, score]);

  const copyToClipboard = (text: string, field: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const titleLength = seoResult?.title ? seoResult.title.length : 0;
  const tagsList = Array.isArray(seoResult?.tags) ? seoResult.tags : [];

  return (
    <div className="h-full flex flex-col p-3 sm:p-6 space-y-3.5 sm:space-y-5 overflow-y-auto">
      {/* Header */}
      <div className="apple-card p-3 sm:p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div className="flex items-center gap-2.5 sm:gap-3">
          <div className="cc-icon orange !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Share2 className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-[var(--text-main)]">Soạn Thảo & Xem Trước SEO</h1>
            <p className="text-xs text-[var(--text-muted)]">
              Tối ưu hóa tiêu đề, mô tả và thẻ tags đạt chuẩn thuật toán đề xuất của YouTube & Facebook Video
            </p>
          </div>
        </div>

        {/* Tournament Switcher */}
        {tournaments.length > 0 && (
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Trophy className="w-4 h-4 text-[var(--accent-blue)] shrink-0" />
            <select
              value={activeTournament?.path || ''}
              onChange={(e) => {
                const t = tournaments.find((item) => item.path === e.target.value);
                if (t) {
                  setActiveTournament(t);
                  setTournamentName(t.name);
                  setSport(t.sportType === 'pickleball' ? 'Pickleball' : 'CauLong');
                }
              }}
              className="w-full sm:w-auto px-3.5 py-1.5 rounded-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)] shadow-sm"
            >
              {tournaments.map((t) => (
                <option key={t.id} value={t.path}>
                  [{t.date}] {t.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Main Grid: Parameters (Left) + Live Preview (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Parameters (5 cols) */}
        <div className="lg:col-span-5 apple-card p-5 space-y-4">
          <div className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider pb-2 border-b border-[var(--border-subtle)] flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[var(--accent-orange)]" />
            <span>Thông Tin Trận Đấu & Giải</span>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
              Tên Giải Đấu:
            </label>
            <input
              type="text"
              value={tournamentName}
              onChange={(e) => setTournamentName(e.target.value)}
              placeholder="VD: GIẢI CẦU LÔNG HỒNG LOAN MỞ RỘNG 2026"
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[var(--accent-blue)]"
            />
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                Bộ Môn:
              </label>
              <select
                value={sport}
                onChange={(e) => setSport(e.target.value)}
                className="w-full px-2 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              >
                <option value="CauLong">Cầu Lông</option>
                <option value="Pickleball">Pickleball</option>
                <option value="Tennis">Tennis</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                Vòng Thi Đấu:
              </label>
              <input
                type="text"
                value={round}
                onChange={(e) => setRound(e.target.value)}
                className="w-full px-2 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                Nội Dung:
              </label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-2 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
          </div>

          <div className="space-y-2">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                Vận Động Viên / Đội A:
              </label>
              <input
                type="text"
                value={playerA}
                onChange={(e) => setPlayerA(e.target.value)}
                placeholder="VD: Nguyễn Tiến Minh / Lê Đức Phát"
                className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">
                Vận Động Viên / Đội B:
              </label>
              <input
                type="text"
                value={playerB}
                onChange={(e) => setPlayerB(e.target.value)}
                placeholder="VD: Hải Đăng / Đình Hoàng"
                className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Sân:</label>
              <input
                type="text"
                value={court}
                onChange={(e) => setCourt(e.target.value)}
                className="w-full px-2 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Tài Trợ:</label>
              <input
                type="text"
                value={sponsor}
                onChange={(e) => setSponsor(e.target.value)}
                className="w-full px-2 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-[var(--text-muted)] mb-1">Tỷ Số:</label>
              <input
                type="text"
                value={score}
                onChange={(e) => setScore(e.target.value)}
                className="w-full px-2 py-1.5 rounded-lg bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--accent-blue)]"
              />
            </div>
          </div>
        </div>

        {/* Live Preview Cards (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* YouTube Video Title Card */}
          <div className="apple-card p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[var(--text-main)] flex items-center gap-2">
                <Video className="w-4 h-4 text-[#ff453a]" />
                <span>Tiêu Đề Video YouTube ({titleLength}/100 ký tự)</span>
                {titleLength > 100 && (
                  <span className="text-[10px] text-[#ff453a] font-semibold px-1.5 py-0.5 rounded bg-[#ff453a]/10">
                    Vượt quá 100 ký tự
                  </span>
                )}
              </span>
              <button
                onClick={() => copyToClipboard(seoResult.title, 'title')}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#242c36] hover:bg-[#2e3743] text-xs text-[var(--text-main)] border border-white/5 transition-colors cursor-pointer"
              >
                {copiedField === 'title' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[#30d158]" />
                    <span className="text-[#30d158]">Đã Chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao Chép</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-3 bg-[var(--bg-input)] rounded-lg border border-[var(--border-subtle)] font-mono text-xs text-[var(--accent-green)] select-text leading-relaxed">
              {seoResult.title || '(Chưa có tiêu đề)'}
            </div>
          </div>

          {/* Description Card */}
          <div className="apple-card p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[var(--text-main)] flex items-center gap-2">
                <FileText className="w-4 h-4 text-[var(--accent-blue)]" />
                <span>Nội Dung Mô Tả (Description Preview)</span>
              </span>
              <button
                onClick={() => copyToClipboard(seoResult.description, 'desc')}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#242c36] hover:bg-[#2e3743] text-xs text-[var(--text-main)] border border-white/5 transition-colors cursor-pointer"
              >
                {copiedField === 'desc' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[#30d158]" />
                    <span className="text-[#30d158]">Đã Chép</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao Chép</span>
                  </>
                )}
              </button>
            </div>

            <div className="p-3 bg-[var(--bg-input)] rounded-lg border border-[var(--border-subtle)] text-xs text-[var(--text-main)] select-text leading-relaxed whitespace-pre-line font-sans max-h-48 overflow-y-auto">
              {seoResult.description || '(Chưa có mô tả)'}
            </div>
          </div>

          {/* Tags */}
          <div className="apple-card p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[var(--text-main)] flex items-center gap-2">
                <Tag className="w-4 h-4 text-[var(--accent-green)]" />
                <span>Danh Sách Thẻ Tags ({tagsList.length} tags)</span>
              </span>
              <button
                onClick={() => copyToClipboard(tagsList.join(', '), 'tags')}
                className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#242c36] hover:bg-[#2e3743] text-xs text-[var(--text-main)] border border-white/5 transition-colors cursor-pointer"
              >
                {copiedField === 'tags' ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-[#30d158]" />
                    <span className="text-[#30d158]">Đã Chép Tags</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Sao Chép CSV</span>
                  </>
                )}
              </button>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {tagsList.length === 0 ? (
                <span className="text-xs text-[var(--text-faint)]">(Chưa có thẻ tags)</span>
              ) : (
                tagsList.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 rounded-md bg-[#242c36] text-[var(--text-main)] text-[11px] font-mono border border-white/5"
                  >
                    #{tag}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
