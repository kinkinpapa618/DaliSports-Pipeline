import React, { useState } from 'react';
import { 
  Trophy, FolderOpen, Play, Clock, Video, Film, CheckCircle2, 
  XCircle, Plus, Search, Filter, ExternalLink, Calendar,
  AlertCircle, Loader2, Sparkles, Link2, Bot, Wand2, ArrowRight, Check,
  Edit3, Save, UploadCloud, RefreshCw
} from 'lucide-react';
import { TournamentInfo } from '../types';

export const slugifyVietnamese = (text: string): string => {
  if (!text) return '';
  // Remove leading date if user typed YYYY-MM-DD_ or YYYY-MM-DD-
  let str = text.trim().replace(/^\d{4}-\d{2}-\d{2}[_-]/, '');
  str = str
    .replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, 'a')
    .replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, 'e')
    .replace(/ì|í|ị|ỉ|ĩ/g, 'i')
    .replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, 'o')
    .replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, 'u')
    .replace(/ỳ|ý|ỵ|ỷ|ỹ/g, 'y')
    .replace(/đ/g, 'd')
    .replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, 'a')
    .replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, 'e')
    .replace(/Ì|Í|Ị|Ỉ|Ĩ/g, 'i')
    .replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, 'o')
    .replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, 'u')
    .replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, 'y')
    .replace(/Đ/g, 'd');

  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
};

interface TournamentsViewProps {
  tournaments: TournamentInfo[];
  onSelectTournamentForTimeline: (tournament: TournamentInfo) => void;
  onSelectTournamentForPipeline: (tournament: TournamentInfo, initialMode?: 'default' | 'source_yup') => void;
  onRefresh: () => void;
}

export const TournamentsView: React.FC<TournamentsViewProps> = ({
  tournaments,
  onSelectTournamentForTimeline,
  onSelectTournamentForPipeline,
  onRefresh,
}) => {
  const [search, setSearch] = useState('');
  const [sportFilter, setSportFilter] = useState<string>('all');
  
  // Modal & Video Link States
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'video' | 'manual'>('video');
  const [videoUrl, setVideoUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  
  // Extracted Data from Agent
  const [extractedData, setExtractedData] = useState<{
    raw_title: string;
    tournament_name: string;
    date: string;
    sport_type: 'badminton' | 'pickleball' | 'tennis' | 'other';
    court?: string;
    category?: string;
    round?: string;
    slug: string;
    folder_name: string;
    duration_seconds?: number;
    thumbnail?: string;
    channel?: string;
  } | null>(null);

  // Manual Creation State (Fallback)
  const [newDate, setNewDate] = useState(new Date().toISOString().split('T')[0]);
  const [newSlug, setNewSlug] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createdResult, setCreatedResult] = useState<{ folderName: string; path: string } | null>(null);

  // Edit Tournament States
  const [editingTournament, setEditingTournament] = useState<TournamentInfo | null>(null);
  const [editName, setEditName] = useState('');
  const [editDate, setEditDate] = useState('');
  const [editSport, setEditSport] = useState<'badminton' | 'pickleball' | 'tennis' | 'other'>('badminton');
  const [editUrl, setEditUrl] = useState('');
  const [editCourt, setEditCourt] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editSponsor, setEditSponsor] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState<string | null>(null);

  const filtered = tournaments.filter((t) => {
    const matchSearch = t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.folderName.toLowerCase().includes(search.toLowerCase()) ||
      t.date.includes(search);
    const matchSport = sportFilter === 'all' || t.sportType === sportFilter;
    return matchSearch && matchSport;
  });

  const totalVideos = tournaments.filter(t => t.hasVideo).length;
  const totalClips = tournaments.reduce((acc, t) => acc + t.clipCount, 0);
  const totalMatches = tournaments.reduce((acc, t) => acc + t.matchCount, 0);

  // Agent Video Analysis Handler
  const handleAnalyzeVideo = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanUrl = videoUrl.trim();
    if (!cleanUrl) {
      setAnalysisError('Vui lòng dán link video YouTube hoặc Facebook.');
      return;
    }

    if (!window.api || typeof window.api.extractVideoInfo !== 'function') {
      setAnalysisError('Không kết nối được với Electron API. Vui lòng chạy ứng dụng qua start_studio.bat.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError(null);
    setExtractedData(null);

    try {
      const res = await window.api.extractVideoInfo(cleanUrl);
      if (res && res.success) {
        setExtractedData({
          raw_title: res.raw_title || '',
          tournament_name: res.tournament_name || 'Giải Đấu Mới',
          date: res.date || new Date().toISOString().split('T')[0],
          sport_type: res.sport_type || 'badminton',
          court: res.court || 'Sân 1',
          category: res.category || 'Đôi Nam',
          round: res.round || 'Vòng Bảng',
          slug: res.slug || slugifyVietnamese(res.tournament_name || 'giai-dau-moi'),
          folder_name: res.folder_name || `${res.date}_${res.slug}`,
          duration_seconds: res.duration_seconds,
          thumbnail: res.thumbnail,
          channel: res.channel,
        });
      } else {
        setAnalysisError(res?.error || 'Không thể trích xuất metadata từ link video. Vui lòng kiểm tra lại URL.');
      }
    } catch (err: any) {
      console.error('Lỗi phân tích video:', err);
      setAnalysisError(err?.message || 'Có lỗi xảy ra khi Agent phân tích video.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Confirm Import & Auto-Insert into Table
  const handleConfirmVideoImport = async () => {
    if (!extractedData) return;
    if (!window.api || typeof window.api.createTournamentFromVideo !== 'function') {
      setAnalysisError('Không tìm thấy API tạo giải đấu.');
      return;
    }

    setIsCreating(true);
    setCreateError(null);

    try {
      const res = await window.api.createTournamentFromVideo({
        date: extractedData.date,
        slug: slugifyVietnamese(extractedData.tournament_name),
        tournamentName: extractedData.tournament_name,
        sportType: extractedData.sport_type,
        url: videoUrl.trim(),
        court: extractedData.court,
        category: extractedData.category,
        round: extractedData.round,
      });

      if (!res || !res.success) {
        setCreateError(res?.error || 'Không thể tạo thư mục giải đấu.');
        setIsCreating(false);
        return;
      }

      setCreatedResult({ folderName: res.folderName, path: res.path });
      setIsCreating(false);
      onRefresh();
    } catch (err: any) {
      console.error('Lỗi khi chèn giải đấu:', err);
      setCreateError(err?.message || 'Có lỗi xảy ra khi tạo giải đấu.');
      setIsCreating(false);
    }
  };

  const handleCreateTournament = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setCreatedResult(null);

    const cleanSlug = slugifyVietnamese(newSlug);
    if (!newDate) {
      setCreateError('Vui lòng chọn ngày thi đấu.');
      return;
    }
    if (!cleanSlug) {
      setCreateError('Vui lòng nhập tên giải đấu (ví dụ: Giai Cau Long Mo Rong).');
      return;
    }

    if (!window.api || typeof window.api.createTournament !== 'function') {
      setCreateError('Không kết nối được với Electron API. Hãy chắc chắn bạn đang thao tác trên cửa sổ ứng dụng DaliSports Studio.');
      return;
    }

    setIsCreating(true);
    try {
      const res = await window.api.createTournament(newDate, cleanSlug);
      if (!res || !res.success) {
        setCreateError(res?.error || 'Không thể tạo thư mục. Vui lòng kiểm tra quyền ghi ổ đĩa.');
        setIsCreating(false);
        return;
      }

      setCreatedResult({ folderName: res.folderName, path: res.path });
      setIsCreating(false);
      onRefresh();
    } catch (err: any) {
      console.error('Lỗi khi tạo giải đấu:', err);
      setCreateError(err?.message || 'Có lỗi xảy ra khi tạo thư mục giải đấu.');
      setIsCreating(false);
    }
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setVideoUrl('');
    setExtractedData(null);
    setAnalysisError(null);
    setNewSlug('');
    setCreateError(null);
    setCreatedResult(null);
    setIsCreating(false);
    setIsAnalyzing(false);
  };

  const handleOpenEdit = (t: TournamentInfo) => {
    setEditingTournament(t);
    setEditName(t.name || '');
    setEditDate(t.date || '');
    setEditSport(t.sportType || 'badminton');
    setEditUrl(t.sourceUrl || '');
    setEditCourt(t.court || 'Sân 1');
    setEditCategory(t.category || 'Đôi Nam');
    setEditSponsor(t.sponsor || '');
    setUpdateError(null);
    setIsUpdating(false);
  };

  const handleCloseEdit = () => {
    setEditingTournament(null);
    setUpdateError(null);
    setIsUpdating(false);
  };

  const handleSaveEdit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!editingTournament) return;
    if (!editName.trim()) {
      setUpdateError('Tên giải đấu không được để trống.');
      return;
    }
    setIsUpdating(true);
    setUpdateError(null);

    if (typeof window.api?.updateTournament !== 'function') {
      setUpdateError('Preload API chưa được nạp. Vui lòng đóng ứng dụng và mở lại (hoặc nhấn Ctrl+R) để nạp các hàm IPC mới.');
      setIsUpdating(false);
      return;
    }

    try {
      const res = await window.api.updateTournament(editingTournament.path, {
        name: editName.trim(),
        date: editDate.trim(),
        sportType: editSport,
        sourceUrl: editUrl.trim(),
        court: editCourt.trim(),
        category: editCategory.trim(),
        sponsor: editSponsor.trim(),
      });

      if (!res || !res.success) {
        setUpdateError(res?.error || 'Không thể lưu thay đổi thông tin giải đấu.');
        setIsUpdating(false);
        return;
      }

      setIsUpdating(false);
      setEditingTournament(null);
      onRefresh();
    } catch (err: any) {
      console.error('Lỗi khi cập nhật giải đấu:', err);
      setUpdateError(err?.message || 'Có lỗi xảy ra khi lưu thông tin giải đấu.');
      setIsUpdating(false);
    }
  };

  const [importingId, setImportingId] = useState<string | null>(null);

  const handleImportVideo = async (t: TournamentInfo) => {
    try {
      setImportingId(t.id);
      // Electron mode: native dialog
      if ((window as any).api?.importVideoFile) {
        const res = await (window as any).api.importVideoFile(t.path);
        if (res?.success) {
          onRefresh();
        } else if (res?.error) {
          alert(res.error);
        }
      } else if ((window as any).api?.importVideoFileDialog) {
        // Web remote mode
        const res = await (window as any).api.importVideoFileDialog(t.path);
        if (res?.success) onRefresh();
      } else {
        // Fallback hidden input for web remote
        const inp = document.createElement('input');
        inp.type = 'file';
        inp.accept = 'video/mp4,video/*,.mp4,.mkv,.mov,.avi,.ts';
        inp.onchange = async () => {
          const file = inp.files?.[0];
          if (!file) { setImportingId(null); return; }
          const form = new FormData();
          form.append('file', file);
          const resp = await fetch(`/api/video/import?tournamentPath=${encodeURIComponent(t.path)}`, { method: 'POST', body: form });
          const data = await resp.json();
          if (data.success) onRefresh();
          else alert(data.error || 'Import thất bại');
          setImportingId(null);
        };
        inp.click();
        // Don't reset immediately, wait for onchange
        return;
      }
    } catch (e: any) {
      alert(e.message || 'Import lỗi');
    } finally {
      setImportingId(null);
    }
  };

  const openFolder = (path: string) => {
    window.api?.openFolder(path);
  };

  return (
    <div className="h-full flex flex-col p-3 sm:p-6 space-y-4 sm:space-y-6 overflow-y-auto">
      {/* Header & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-black tracking-tight text-[var(--text-main)] flex items-center gap-2.5 sm:gap-3">
            <Trophy className="w-6 h-6 sm:w-7 sm:h-7 text-[var(--accent-blue)] shrink-0" />
            <span>Quản Lý Giải Đấu & Video</span>
          </h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 sm:mt-1">
            Theo dõi video nguồn, tệp timeline bóc tách tỷ số AI, clips cắt highlight và lịch sử tải lên
          </p>
        </div>

        {/* NÚT NHẬP LINK VIDEO & QUICK REFRESH */}
        <div className="flex items-center gap-2 sm:gap-2.5">
          <button
            onClick={() => {
              setShowModal(true);
              setModalMode('video');
              setAnalysisError(null);
              setExtractedData(null);
              setCreatedResult(null);
            }}
            className="btn-blue cursor-pointer flex-1 sm:flex-none justify-center"
          >
            <Link2 className="w-4 h-4" />
            <span>Nhập Link Video</span>
            <span className="px-2 py-0.5 rounded-full bg-white/20 text-[10px] uppercase font-mono tracking-wider font-extrabold">
              Agent AI
            </span>
          </button>

          <button
            onClick={onRefresh}
            className="circle-btn !w-9 !h-9 shrink-0"
            title="Làm mới danh sách giải đấu"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-4">
        <div className="apple-card p-3 sm:p-4 flex items-center gap-2.5 sm:gap-4">
          <div className="cc-icon blue !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Trophy className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] sm:text-[11px] text-[var(--text-muted)] font-medium truncate">Tổng Giải Đấu</div>
            <div className="text-lg sm:text-xl font-bold text-[var(--text-main)] font-mono">{tournaments.length}</div>
          </div>
        </div>

        <div className="apple-card p-3 sm:p-4 flex items-center gap-2.5 sm:gap-4">
          <div className="cc-icon blue !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Video className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] sm:text-[11px] text-[var(--text-muted)] font-medium truncate">Video Có Sẵn</div>
            <div className="text-lg sm:text-xl font-bold text-[var(--text-main)] font-mono">{totalVideos}</div>
          </div>
        </div>

        <div className="apple-card p-3 sm:p-4 flex items-center gap-2.5 sm:gap-4">
          <div className="cc-icon orange !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Clock className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] sm:text-[11px] text-[var(--text-muted)] font-medium truncate">Trận Gemini AI</div>
            <div className="text-lg sm:text-xl font-bold text-[var(--text-main)] font-mono">{totalMatches}</div>
          </div>
        </div>

        <div className="apple-card p-3 sm:p-4 flex items-center gap-2.5 sm:gap-4">
          <div className="cc-icon green !w-9 !h-9 sm:!w-10 sm:!h-10 !rounded-xl text-white shrink-0">
            <Film className="w-4 h-4 sm:w-5 sm:h-5" />
          </div>
          <div className="min-w-0">
            <div className="text-[10px] sm:text-[11px] text-[var(--text-muted)] font-medium truncate">Clips Đã Cắt</div>
            <div className="text-lg sm:text-xl font-bold text-[var(--text-main)] font-mono">{totalClips}</div>
          </div>
        </div>
      </div>

      {/* Filter & Search Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5 sm:gap-3 p-1">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--text-faint)]" />
          <input
            type="text"
            placeholder="Tìm kiếm giải đấu, ngày hoặc tên thư mục..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 rounded-full bg-[var(--bg-input)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] placeholder-[var(--text-faint)] focus:outline-none focus:border-[var(--accent-blue)] shadow-sm transition-colors"
          />
        </div>

        <div className="tab-bar overflow-x-auto no-scrollbar w-full sm:w-auto justify-start sm:justify-end flex-nowrap">
          <button
            onClick={() => setSportFilter('all')}
            className={`tab-item shrink-0 ${sportFilter === 'all' ? 'active' : ''}`}
          >
            Tất Cả
          </button>
          <button
            onClick={() => setSportFilter('badminton')}
            className={`tab-item shrink-0 ${sportFilter === 'badminton' ? 'active' : ''}`}
          >
            🏸 Cầu Lông
          </button>
          <button
            onClick={() => setSportFilter('pickleball')}
            className={`tab-item shrink-0 ${sportFilter === 'pickleball' ? 'active' : ''}`}
          >
            🏓 Pickleball
          </button>
        </div>
      </div>

      {/* Tournaments Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
        {filtered.map((t) => (
          <div
            key={t.id}
            className="apple-card p-3.5 sm:p-5 flex flex-col justify-between space-y-3 sm:space-y-4 group"
          >
            {/* Top row */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-[var(--bg-input)] text-[var(--text-muted)] flex items-center gap-1.5 border border-[var(--border-subtle)]">
                  <Calendar className="w-3 h-3 text-[var(--text-muted)]" />
                  {t.date}
                </span>

                <div className="flex items-center gap-1.5">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                      t.sportType === 'pickleball'
                        ? 'bg-[#ff9f0a]/15 border-[#ff9f0a]/30 text-[#ff9f0a]'
                        : 'bg-[#0a84ff]/15 border-[#0a84ff]/30 text-[#0a84ff]'
                    }`}
                  >
                    {t.sportType === 'pickleball' ? '🏓 Pickleball' : '🏸 Cầu Lông'}
                  </span>

                  <button
                    onClick={() => handleOpenEdit(t)}
                    className="circle-btn !w-7 !h-7 text-xs !shadow-none hover:!text-[#ff9f0a]"
                    title="Chỉnh sửa thông tin giải đấu"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                  </button>

                  <button
                    onClick={() => openFolder(t.path)}
                    className="circle-btn !w-7 !h-7 text-xs !shadow-none hover:!text-[#0a84ff]"
                    title="Mở thư mục trên máy tính"
                  >
                    <FolderOpen className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <h3 className="text-sm font-bold text-[var(--text-main)] group-hover:text-[var(--accent-blue)] transition-colors line-clamp-2 leading-snug">
                {t.name}
              </h3>
              <p className="text-[11px] text-[var(--text-muted)] font-mono truncate">{t.folderName}</p>
              {t.sourceUrl && (
                <div className="flex items-center gap-1.5 text-[11px] font-mono truncate pt-0.5">
                  <Link2 className="w-3 h-3 shrink-0 text-[var(--accent-blue)]" />
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      window.api?.openUrl(t.sourceUrl!);
                    }}
                    className="truncate hover:underline cursor-pointer text-[var(--text-muted)] hover:text-[var(--accent-blue)]"
                    title={`Mở link video: ${t.sourceUrl}`}
                  >
                    {t.sourceUrl}
                  </span>
                </div>
              )}

              {(t.court || t.category || t.sponsor) && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1">
                  {t.court && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#30d158]/15 text-[#30d158] font-medium border border-[#30d158]/20">
                      {t.court}
                    </span>
                  )}
                  {t.category && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#0a84ff]/15 text-[#0a84ff] font-medium border border-[#0a84ff]/20">
                      {t.category}
                    </span>
                  )}
                  {t.sponsor && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#ff9f0a]/15 text-[#ff9f0a] font-medium border border-[#ff9f0a]/20 truncate max-w-[150px]" title={`Nhà tài trợ: ${t.sponsor}`}>
                      ★ {t.sponsor}
                    </span>
                  )}
                </div>
              )}
            </div>

            {/* Status indicators */}
            <div className="grid grid-cols-2 gap-2 py-2 border-y border-[var(--border-subtle)] text-xs">
              <div className="flex items-center gap-2">
                <Video className={`w-3.5 h-3.5 ${t.hasVideo ? 'text-[#30d158]' : 'text-[var(--text-faint)]'}`} />
                <span className="text-[var(--text-muted)]">Video:</span>
                <span className={`font-mono ${t.hasVideo ? 'text-[var(--text-main)]' : 'text-[var(--text-faint)]'}`}>
                  {t.hasVideo ? `${t.videoSizeMb}MB` : 'Chưa có'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <Clock className={`w-3.5 h-3.5 ${t.hasTimeline ? 'text-[#30d158]' : 'text-[var(--text-faint)]'}`} />
                <span className="text-[var(--text-muted)]">Timeline:</span>
                <span className={`font-mono ${t.hasTimeline ? 'text-[#30d158] font-bold' : 'text-[var(--text-faint)]'}`}>
                  {t.hasTimeline ? `${t.matchCount} trận` : 'Chưa có'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <Film className={`w-3.5 h-3.5 ${t.hasClips ? 'text-[#30d158]' : 'text-[var(--text-faint)]'}`} />
                <span className="text-[var(--text-muted)]">Clips:</span>
                <span className={`font-mono ${t.hasClips ? 'text-[#30d158] font-bold' : 'text-[var(--text-faint)]'}`}>
                  {t.hasClips ? `${t.clipCount} files` : '0'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {t.uploadedYoutube ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#30d158]" />
                ) : (
                  <XCircle className="w-3.5 h-3.5 text-[var(--text-faint)]" />
                )}
                <span className="text-[var(--text-muted)]">Đã Upload:</span>
                <span className="font-mono text-[var(--text-main)]">
                  {t.uploadedYoutube ? 'YouTube' : 'Chưa'}
                </span>
              </div>
            </div>

            {/* Import trực tiếp (1) - độc lập */}
            <div className="flex gap-1.5">
              <button
                onClick={() => handleImportVideo(t)}
                disabled={importingId === t.id}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-full bg-[#30d158]/10 hover:bg-[#30d158]/20 border border-[#30d158]/25 text-[#30d158] text-[11px] font-bold transition-colors disabled:opacity-50"
                title="Import file video trực tiếp vào giải (bước 1 độc lập)"
              >
                <UploadCloud className="w-3 h-3 shrink-0" />
                <span>{t.hasVideo ? 'Đổi Video' : 'Import Video'}</span>
                {importingId === t.id && <Loader2 className="w-3 h-3 animate-spin" />}
              </button>
              <span className="text-[10px] px-2 py-1 rounded-full bg-slate-800 text-slate-400 font-mono self-center border border-white/5">Bước 1</span>
            </div>

            {/* Actions: CHẠY FULL - TIMELINE - Y-UPLOAD (bước 2-4) */}
            <div className="grid grid-cols-3 gap-1.5 sm:gap-2 pt-1">
              <button
                onClick={() => onSelectTournamentForPipeline(t)}
                className="flex items-center justify-center gap-1 py-2 px-1 rounded-full bg-[#0a84ff] hover:bg-[#0071e3] text-white text-[11px] sm:text-xs font-bold transition-all shadow-md shadow-[#0a84ff]/20 cursor-pointer"
                title="Khởi chạy toàn bộ pipeline (cắt clip và xuất bản) - tuần tự 4 bước"
              >
                <Play className="w-3 h-3 sm:w-3.5 sm:h-3.5 fill-current shrink-0" />
                <span className="truncate">CHẠY FULL</span>
              </button>

              <button
                onClick={() => onSelectTournamentForTimeline(t)}
                className="flex items-center justify-center gap-1 py-2 px-1 rounded-full bg-[#242c36] hover:bg-[#2e3743] text-[var(--text-main)] text-[11px] sm:text-xs font-semibold border border-white/5 transition-colors shadow-sm cursor-pointer"
                title="Xem hoặc chỉnh sửa timeline trận đấu"
              >
                <Clock className="w-3 h-3 sm:w-3.5 sm:h-3.5 text-[var(--text-muted)] shrink-0" />
                <span className="truncate">TIMELINE</span>
              </button>

              <button
                onClick={() => onSelectTournamentForPipeline(t, 'source_yup')}
                className="flex items-center justify-center gap-1 py-2 px-1 rounded-full bg-[#ff9f0a]/15 hover:bg-[#ff9f0a]/25 text-[#ff9f0a] text-[11px] sm:text-xs font-bold border border-[#ff9f0a]/30 transition-all shadow-sm cursor-pointer"
                title="Upload Video Nguồn Full lên YouTube kèm Chapters (Y-UPLOAD)"
              >
                <UploadCloud className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0" />
                <span className="truncate">Y-UPLOAD</span>
              </button>
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="col-span-full text-center py-16 text-slate-400">
            <Trophy className="w-12 h-12 mx-auto mb-3 opacity-20" />
            <p className="text-sm font-medium">Không tìm thấy giải đấu nào phù hợp.</p>
          </div>
        )}
      </div>

      {/* Modal: Nhập Link Video & Agent Tự Động Lọc Dữ Liệu */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="apple-card w-full max-w-xl p-4 sm:p-6 space-y-4 shadow-2xl animate-in fade-in slide-in-from-bottom-6 sm:zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
                  {modalMode === 'video' ? <Link2 className="w-4 h-4" /> : <Plus className="w-4 h-4" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>{modalMode === 'video' ? 'Nhập Link Video - Agent Tự Động Lọc Dữ Liệu' : 'Tạo Thư Mục Giải Đấu Thủ Công'}</span>
                    {modalMode === 'video' && (
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono font-extrabold">
                        AGENT AI
                      </span>
                    )}
                  </h3>
                  <p className="text-[11px] text-slate-400">
                    {modalMode === 'video'
                      ? 'Dán liên kết YouTube hoặc Facebook, Agent sẽ tự động phân tích & chèn vào bảng.'
                      : 'Nhập ngày và tên giải đấu để khởi tạo thư mục cấu trúc thủ công.'}
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseModal}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Success State */}
            {createdResult ? (
              <div className="space-y-4 py-3">
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <div className="text-sm font-bold text-emerald-300">Đã chèn giải đấu vào bảng thành công!</div>
                    <div className="text-xs font-mono text-emerald-200 break-all">{createdResult.folderName}</div>
                    <p className="text-[11px] text-slate-400 pt-1">
                      Đã tự động khởi tạo cấu trúc: <code>video/</code>, <code>clips/</code>, <code>thumbnails/</code> và file <code>timeline.json</code>. Giải đấu đã sẵn sàng trên bảng.
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => openFolder(createdResult.path)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
                  >
                    <FolderOpen className="w-4 h-4 text-amber-400" />
                    <span>Mở Thư Mục</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-colors"
                  >
                    Hoàn Tất & Xem Bảng
                  </button>
                </div>
              </div>
            ) : modalMode === 'video' ? (
              /* VIDEO LINK MODE */
              <div className="space-y-4">
                {analysisError && (
                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start gap-2.5 text-xs text-rose-300">
                    <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{analysisError}</span>
                  </div>
                )}

                {/* Video URL Input */}
                <div className="space-y-1.5">
                  <label className="block text-xs font-semibold text-slate-300 flex items-center justify-between">
                    <span className="flex items-center gap-1.5">
                      <Link2 className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Đường dẫn video / Livestream (YouTube hoặc Facebook):</span>
                    </span>
                    <span className="text-[11px] text-slate-400 font-normal">Hỗ trợ link live & video dài</span>
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="url"
                      placeholder="Dán link (vd: https://www.youtube.com/watch?v=... hoặc Facebook Video)"
                      value={videoUrl}
                      onChange={(e) => setVideoUrl(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          handleAnalyzeVideo();
                        }
                      }}
                      className="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                    />
                    <button
                      type="button"
                      onClick={() => handleAnalyzeVideo()}
                      disabled={isAnalyzing || !videoUrl.trim()}
                      className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                    >
                      {isAnalyzing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Đang Phân Tích...</span>
                        </>
                      ) : (
                        <>
                          <Sparkles className="w-3.5 h-3.5" />
                          <span>Lọc Dữ Liệu</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Analyzing State Indicator */}
                {isAnalyzing && (
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 flex items-center gap-3 animate-pulse">
                    <Bot className="w-5 h-5 text-emerald-400 animate-bounce shrink-0" />
                    <div className="space-y-0.5">
                      <div className="text-xs font-bold text-slate-200">Agent đang phân tích & trích xuất metadata...</div>
                      <div className="text-[11px] text-slate-400">Đọc tiêu đề, ngày tải lên, môn thể thao và chuẩn hóa tên giải qua yt-dlp...</div>
                    </div>
                  </div>
                )}

                {/* Extracted Data Card */}
                {extractedData && !isAnalyzing && (
                  <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-3.5 animate-in fade-in zoom-in-95 duration-200">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                      <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Dữ Liệu Đã Được Agent Tự Động Lọc</span>
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        {extractedData.sport_type.toUpperCase()}
                      </span>
                    </div>

                    {/* Raw Title Reference */}
                    <div className="text-[11px] text-slate-400 bg-slate-900/60 p-2 rounded-lg border border-slate-800/80 line-clamp-2">
                      <strong className="text-slate-300">Tiêu đề gốc:</strong> {extractedData.raw_title}
                    </div>

                    {/* Editable Extracted Fields */}
                    <div className="space-y-2.5 text-xs">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                          Tên Giải Đấu (Agent đã chuẩn hóa loại bỏ từ thừa):
                        </label>
                        <input
                          type="text"
                          value={extractedData.tournament_name}
                          onChange={(e) => setExtractedData({ ...extractedData, tournament_name: e.target.value })}
                          className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500 font-semibold"
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                            Ngày Thi Đấu:
                          </label>
                          <input
                            type="date"
                            value={extractedData.date}
                            onChange={(e) => setExtractedData({ ...extractedData, date: e.target.value })}
                            className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                          />
                        </div>

                        <div>
                          <label className="block text-[11px] font-semibold text-slate-400 mb-1">
                            Môn Thể Thao:
                          </label>
                          <select
                            value={extractedData.sport_type}
                            onChange={(e) => setExtractedData({ ...extractedData, sport_type: e.target.value as any })}
                            className="w-full px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-emerald-500"
                          >
                            <option value="badminton">🏸 Cầu Lông</option>
                            <option value="pickleball">🏓 Pickleball</option>
                            <option value="tennis">🎾 Tennis</option>
                            <option value="other">Thể Thao Khác</option>
                          </select>
                        </div>
                      </div>

                      {/* Additional Tags (Court, Category, Round) */}
                      <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px] font-mono text-slate-400">
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {extractedData.court || 'Sân 1'}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {extractedData.category || 'Đôi Nam'}
                        </span>
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
                          {extractedData.round || 'Vòng Bảng'}
                        </span>
                      </div>

                      {/* Folder Slug Preview */}
                      <div className="pt-1">
                        <div className="text-[10px] text-slate-400 font-mono">
                          📁 Thư mục tạo tự động: <span className="text-emerald-400 font-bold">{extractedData.date}_{slugifyVietnamese(extractedData.tournament_name)}</span>
                        </div>
                      </div>
                    </div>

                    {/* Action button */}
                    <div className="pt-2">
                      <button
                        type="button"
                        onClick={handleConfirmVideoImport}
                        disabled={isCreating}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all cursor-pointer disabled:opacity-50"
                      >
                        {isCreating ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Đang khởi tạo thư mục & chèn vào bảng...</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-4 h-4 stroke-[3]" />
                            <span>Xác Nhận & Chèn Vào Bảng Giải Đấu</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}

                {/* Bottom Switcher: Chưa có link video -> Nhập thủ công */}
                <div className="text-center pt-2 border-t border-slate-800/80">
                  <button
                    type="button"
                    onClick={() => setModalMode('manual')}
                    className="text-xs text-slate-400 hover:text-emerald-400 transition-colors underline underline-offset-2"
                  >
                    Chưa có link video? Nhập tên thư mục giải đấu thủ công tại đây
                  </button>
                </div>
              </div>
            ) : (
              /* MANUAL FALLBACK MODE */
              <form onSubmit={handleCreateTournament} className="space-y-4">
                {createError && (
                  <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 flex items-start gap-2.5 text-xs text-rose-300">
                    <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    <span className="leading-relaxed">{createError}</span>
                  </div>
                )}

                {/* Quick Sport Selector */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    <span>Chọn nhanh môn thể thao:</span>
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        if (!newSlug || newSlug.includes('pickleball')) {
                          setNewSlug('giai-cau-long-');
                        }
                      }}
                      className="px-3 py-2 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
                    >
                      <span>🏸 Cầu Lông</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        if (!newSlug || newSlug.includes('cau-long')) {
                          setNewSlug('giai-pickleball-');
                        }
                      }}
                      className="px-3 py-2 rounded-lg bg-orange-500/10 hover:bg-orange-500/20 border border-orange-500/30 text-orange-300 text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
                    >
                      <span>🏓 Pickleball</span>
                    </button>
                  </div>
                </div>

                {/* Date Input */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Ngày thi đấu:
                  </label>
                  <input
                    type="date"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>

                {/* Name / Slug Input */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Tên giải đấu (hỗ trợ gõ tiếng Việt có dấu):
                  </label>
                  <input
                    type="text"
                    placeholder="ví dụ: Giải Cầu Lông Ba Vì Mở Rộng 2026"
                    value={newSlug}
                    onChange={(e) => setNewSlug(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-emerald-500"
                    required
                  />
                </div>

                {/* Real-time Preview Box */}
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1.5">
                  <div className="text-[11px] text-slate-400 font-medium flex items-center gap-1.5">
                    <FolderOpen className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Xem trước thư mục sẽ được tạo:</span>
                  </div>
                  <div className="font-mono text-emerald-400 font-bold text-xs break-all bg-emerald-500/5 px-2 py-1.5 rounded border border-emerald-500/20">
                    {newDate}_{slugifyVietnamese(newSlug) || 'ten-giai-dau'}
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Tự động tạo các thư mục: <code>video/</code>, <code>clips/</code>, <code>thumbnails/</code> và file khởi tạo <code>timeline.json</code>.
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={() => setModalMode('video')}
                    className="text-xs text-emerald-400 hover:underline"
                  >
                    ← Quay lại nhập link video
                  </button>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleCloseModal}
                      disabled={isCreating}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
                    >
                      Hủy
                    </button>
                    <button
                      type="submit"
                      disabled={isCreating || !newSlug.trim()}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isCreating ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Đang tạo thư mục...</span>
                        </>
                      ) : (
                        <>
                          <Plus className="w-3.5 h-3.5 stroke-[3]" />
                          <span>Tạo Thư Mục</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Modal: Chỉnh Sửa Thông Tin Giải Đấu */}
      {editingTournament && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="apple-card w-full max-w-xl p-4 sm:p-6 space-y-4 shadow-2xl animate-in fade-in slide-in-from-bottom-6 sm:zoom-in-95 duration-200 max-h-[90vh] overflow-y-auto rounded-t-2xl sm:rounded-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <Edit3 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white flex items-center gap-2">
                    <span>Chỉnh Sửa Thông Tin Giải Đấu</span>
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {editingTournament.folderName}
                  </p>
                </div>
              </div>
              <button
                onClick={handleCloseEdit}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            {/* Error Alert */}
            {updateError && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{updateError}</span>
              </div>
            )}

            {/* Edit Form */}
            <form onSubmit={handleSaveEdit} className="space-y-4">
              {/* Tên giải đấu */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Tên Giải Đấu <span className="text-red-400">*</span>
                </label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Ví dụ: GIẢI CẦU LÔNG CLB KINH MÔN MỞ RỘNG 2026"
                  className="w-full px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                  required
                />
              </div>

              {/* Ngày & Môn thi đấu */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Ngày Thi Đấu</label>
                  <input
                    type="date"
                    value={editDate}
                    onChange={(e) => setEditDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Bộ Môn</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setEditSport('badminton')}
                      className={`py-2 px-2.5 rounded-lg border text-xs font-semibold transition-all ${
                        editSport === 'badminton'
                          ? 'bg-blue-500/20 border-blue-500/50 text-blue-300 shadow-sm shadow-blue-500/20'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-300'
                      }`}
                    >
                      🏸 Cầu Lông
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditSport('pickleball')}
                      className={`py-2 px-2.5 rounded-lg border text-xs font-semibold transition-all ${
                        editSport === 'pickleball'
                          ? 'bg-orange-500/20 border-orange-500/50 text-orange-300 shadow-sm shadow-orange-500/20'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-300'
                      }`}
                    >
                      🏓 Pickleball
                    </button>
                  </div>
                </div>
              </div>

              {/* Link Video Nguồn */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                  <span>Link Video Nguồn (YouTube / Facebook)</span>
                  {editUrl && (
                    <button
                      type="button"
                      onClick={() => window.api?.openUrl(editUrl)}
                      className="text-[11px] text-teal-400 hover:underline flex items-center gap-1"
                    >
                      <ExternalLink className="w-3 h-3" />
                      Mở link
                    </button>
                  )}
                </label>
                <div className="relative">
                  <Link2 className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="url"
                    value={editUrl}
                    onChange={(e) => setEditUrl(e.target.value)}
                    placeholder="https://www.youtube.com/watch?v=... hoặc https://www.facebook.com/..."
                    className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                  />
                </div>
              </div>

              {/* Sân & Nội Dung mặc định */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Sân Mặc Định</label>
                  <input
                    type="text"
                    value={editCourt}
                    onChange={(e) => setEditCourt(e.target.value)}
                    placeholder="Ví dụ: Sân 1, Sân Trung Tâm"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300">Nội Dung Mặc Định</label>
                  <input
                    type="text"
                    value={editCategory}
                    onChange={(e) => setEditCategory(e.target.value)}
                    placeholder="Ví dụ: Đôi Nam, Đôi Nữ, Đơn Nam"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                  />
                </div>
              </div>

              {/* Nhà Tài Trợ */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">Nhà Tài Trợ / Đối Tác</label>
                <input
                  type="text"
                  value={editSponsor}
                  onChange={(e) => setEditSponsor(e.target.value)}
                  placeholder="Ví dụ: DaliSports, Yonex, Kamito, Victor..."
                  className="w-full px-3 py-2 rounded-lg bg-slate-950/80 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-amber-500/50"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={handleCloseEdit}
                  disabled={isUpdating}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors cursor-pointer disabled:opacity-50"
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  disabled={isUpdating || !editName.trim()}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-amber-500/20"
                >
                  {isUpdating ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Đang lưu...</span>
                    </>
                  ) : (
                    <>
                      <Save className="w-3.5 h-3.5" />
                      <span>Lưu Thay Đổi</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
