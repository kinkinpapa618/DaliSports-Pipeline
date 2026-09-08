/// <reference types="vite/client" />

import { MatchTimelineItem, PipelineLogMessage, PipelineOptions, SeoPreviewResult, TournamentInfo, UpdateCheckResult, ApplyUpdateResult } from '../electron/types';

declare global {
  interface Window {
    api: {
      isWeb?: boolean;
      scanTournaments: () => Promise<TournamentInfo[]>;
      createTournament: (date: string, slug: string) => Promise<{ success: boolean; folderName: string; path: string; error?: string }>;
      updateTournament: (tournamentPath: string, updates: any) => Promise<{ success: boolean; error?: string }>;
      extractVideoInfo: (url: string) => Promise<any>;
      createTournamentFromVideo: (data: any) => Promise<{ success: boolean; folderName: string; path: string; error?: string }>;
      openFolder: (dirPath: string) => Promise<void>;
      openUrl: (url: string) => Promise<void>;

      getTimeline: (tournamentPath: string) => Promise<{ matches: MatchTimelineItem[]; rawJson?: any; detectedFile?: string }>;
      saveTimeline: (tournamentPath: string, matches: MatchTimelineItem[]) => Promise<boolean>;

      startPipeline: (options: PipelineOptions) => Promise<boolean>;
      killPipeline: () => Promise<void>;
      isPipelineRunning: () => Promise<boolean>;
      onPipelineLog: (callback: (log: PipelineLogMessage) => void) => void;
      onPipelineExit: (callback: (code: number | null) => void) => void;

      getSeoPreview: (params: any) => Promise<SeoPreviewResult>;

      getConfig: () => Promise<any>;
      saveConfig: (updates: any) => Promise<boolean>;

      checkForUpdates: (customUrl?: string) => Promise<UpdateCheckResult>;
      getCurrentVersion: () => Promise<string>;
      applyUpdate: () => Promise<ApplyUpdateResult>;
      restartApp: () => Promise<void>;

      getTunnelStatus: () => Promise<{ active: boolean; url?: string; error?: string }>;
      startTunnel: () => Promise<{ success: boolean; url?: string; error?: string }>;
      stopTunnel: () => Promise<{ success: boolean }>;

      windowMinimize: () => void;
      windowMaximize: () => void;
      windowClose: () => void;
    };
  }
}
