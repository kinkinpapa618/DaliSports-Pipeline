import React, { useState, useEffect } from 'react';
import { TitleBar } from './components/TitleBar';
import { Sidebar } from './components/Sidebar';
import { TournamentsView } from './views/TournamentsView';
import { TimelineEditorView } from './views/TimelineEditorView';
import { PipelineConsoleView } from './views/PipelineConsoleView';
import { SeoPreviewView } from './views/SeoPreviewView';
import { SettingsView } from './views/SettingsView';
import { ActiveTab, TournamentInfo, UpdateCheckResult } from './types';
import { useSkin } from './hooks/useSkin';
import { UpdateModal } from './components/UpdateModal';

export const App: React.FC = () => {
  const { skin, setSkin, toggleSkin } = useSkin();
  const [currentTab, setCurrentTab] = useState<ActiveTab>('tournaments');
  const [tournaments, setTournaments] = useState<TournamentInfo[]>([]);
  const [selectedTournament, setSelectedTournament] = useState<TournamentInfo | null>(null);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);

  // Update System State
  const [updateInfo, setUpdateInfo] = useState<UpdateCheckResult | null>(null);
  const [isUpdateModalOpen, setIsUpdateModalOpen] = useState(false);

  // Load tournaments on startup
  const fetchTournaments = async () => {
    try {
      if (window.api) {
        const list = await window.api.scanTournaments();
        setTournaments(list);
        if (!selectedTournament && list.length > 0) {
          setSelectedTournament(list[0]);
        }
      }
    } catch (err) {
      console.error('Failed to load tournaments:', err);
    }
  };

  useEffect(() => {
    fetchTournaments();

    // Check pipeline running status
    window.api?.isPipelineRunning().then((running) => {
      setIsPipelineRunning(running);
    });

    // Check for updates on startup (silent background check)
    window.api?.checkForUpdates?.().then((res) => {
      if (res && res.hasUpdate) {
        setUpdateInfo(res);
      }
    }).catch((err) => {
      console.warn('[App] Update check failed silently:', err);
    });
  }, []);

  const [pipelineInitialMode, setPipelineInitialMode] = useState<'default' | 'source_yup'>('default');

  // Handlers for cross-view navigation
  const handleSelectForTimeline = (tournament: TournamentInfo) => {
    setSelectedTournament(tournament);
    setCurrentTab('timeline');
  };

  const handleSelectForPipeline = (tournament: TournamentInfo, mode: 'default' | 'source_yup' = 'default') => {
    setSelectedTournament(tournament);
    setPipelineInitialMode(mode);
    setCurrentTab('pipeline');
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#14181d] text-[#e0e0e0] overflow-hidden font-sans">
      {/* Frameless Window Custom Titlebar */}
      <TitleBar 
        isPipelineRunning={isPipelineRunning} 
        skin={skin}
        onToggleSkin={toggleSkin}
        updateInfo={updateInfo}
        onOpenUpdateModal={() => setIsUpdateModalOpen(true)}
      />

      {/* Warning when opened in regular browser instead of Electron */}
      {!window.api && (
        <div className="bg-amber-500/15 border-b border-amber-500/30 px-4 py-2 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center gap-2">
            <span className="font-bold">⚠️ Lưu ý:</span>
            <span>Bạn đang xem trên trình duyệt web. Để tạo thư mục và chạy video pipeline, hãy thao tác trên cửa sổ ứng dụng <strong>DaliSports Studio</strong> mở qua <code>start_studio.bat</code>.</span>
          </div>
        </div>
      )}

      {/* Main Container */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Navigation Sidebar */}
        <Sidebar
          currentTab={currentTab}
          onTabChange={setCurrentTab}
          tournamentCount={tournaments.length}
          isPipelineRunning={isPipelineRunning}
          onRefresh={fetchTournaments}
          skin={skin}
          onToggleSkin={toggleSkin}
        />

        {/* Central Work Area */}
        <main className="flex-1 overflow-hidden bg-[#14181d] relative">
          {currentTab === 'tournaments' && (
            <TournamentsView
              tournaments={tournaments}
              onSelectTournamentForTimeline={handleSelectForTimeline}
              onSelectTournamentForPipeline={handleSelectForPipeline}
              onRefresh={fetchTournaments}
            />
          )}

          {currentTab === 'timeline' && (
            <TimelineEditorView
              tournaments={tournaments}
              selectedTournament={selectedTournament}
              onSelectTournament={setSelectedTournament}
              onNavigateToPipeline={handleSelectForPipeline}
            />
          )}

          {currentTab === 'pipeline' && (
            <PipelineConsoleView
              tournaments={tournaments}
              selectedTournament={selectedTournament}
              onSelectTournament={setSelectedTournament}
              isPipelineRunning={isPipelineRunning}
              setIsPipelineRunning={setIsPipelineRunning}
              initialMode={pipelineInitialMode}
            />
          )}

          {currentTab === 'seo' && (
            <SeoPreviewView
              tournaments={tournaments}
              selectedTournament={selectedTournament}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsView 
              skin={skin}
              onSetSkin={setSkin}
              onUpdateDetected={(info) => {
                setUpdateInfo(info);
                setIsUpdateModalOpen(true);
              }}
            />
          )}
        </main>
      </div>

      {/* Interactive Update Modal */}
      <UpdateModal
        isOpen={isUpdateModalOpen}
        onClose={() => setIsUpdateModalOpen(false)}
        updateInfo={updateInfo}
      />
    </div>
  );
};
export default App;
