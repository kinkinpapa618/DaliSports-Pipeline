import { contextBridge, ipcRenderer } from 'electron';
import { MatchTimelineItem, PipelineLogMessage, PipelineOptions, SeoPreviewResult, TournamentInfo, UpdateCheckResult } from './types';

contextBridge.exposeInMainWorld('api', {
  // Tournaments
  scanTournaments: (): Promise<TournamentInfo[]> => ipcRenderer.invoke('tournaments:scan'),
  createTournament: (date: string, slug: string): Promise<any> => ipcRenderer.invoke('tournaments:create', date, slug),
  updateTournament: (tournamentPath: string, updates: any): Promise<{ success: boolean; error?: string }> =>
    ipcRenderer.invoke('tournaments:update', tournamentPath, updates),
  extractVideoInfo: (url: string): Promise<any> => ipcRenderer.invoke('video:extractInfo', url),
  createTournamentFromVideo: (data: any): Promise<any> => ipcRenderer.invoke('tournaments:createFromVideo', data),
  openFolder: (dirPath: string): Promise<void> => ipcRenderer.invoke('system:openFolder', dirPath),
  openUrl: (url: string): Promise<void> => ipcRenderer.invoke('system:openUrl', url),

  // Timeline
  getTimeline: (tournamentPath: string): Promise<{ matches: MatchTimelineItem[]; rawJson?: any }> => 
    ipcRenderer.invoke('timeline:get', tournamentPath),
  saveTimeline: (tournamentPath: string, matches: MatchTimelineItem[]): Promise<boolean> => 
    ipcRenderer.invoke('timeline:save', tournamentPath, matches),
  generateTimeline: (tournamentPath: string): Promise<any> => ipcRenderer.invoke('timeline:generate', tournamentPath),
  normalizeTimeline: (tournamentPath: string): Promise<any> => ipcRenderer.invoke('timeline:normalize', tournamentPath),
  previewChapters: (tournamentPath: string): Promise<any> => ipcRenderer.invoke('chapters:preview', tournamentPath),

  // Download / Import trực tiếp
  importVideoFile: (tournamentPath: string): Promise<any> => ipcRenderer.invoke('video:importFile', tournamentPath),
  importVideoFilePath: (tournamentPath: string, sourcePath: string): Promise<any> => ipcRenderer.invoke('video:importFilePath', tournamentPath, sourcePath),

  // Pipeline
  startPipeline: (options: PipelineOptions): Promise<boolean> => ipcRenderer.invoke('pipeline:start', options),
  killPipeline: (): Promise<void> => ipcRenderer.invoke('pipeline:kill'),
  isPipelineRunning: (): Promise<boolean> => ipcRenderer.invoke('pipeline:isRunning'),
  onPipelineLog: (callback: (log: PipelineLogMessage) => void) => {
    ipcRenderer.on('pipeline:log', (_: any, log: PipelineLogMessage) => callback(log));
  },
  onPipelineExit: (callback: (code: number | null) => void) => {
    ipcRenderer.on('pipeline:exit', (_: any, code: number | null) => callback(code));
  },

  // SEO Preview
  getSeoPreview: (params: any): Promise<SeoPreviewResult> => ipcRenderer.invoke('seo:preview', params),

  // Config (.env)
  getConfig: (): Promise<any> => ipcRenderer.invoke('config:get'),
  saveConfig: (updates: any): Promise<boolean> => ipcRenderer.invoke('config:save', updates),

  // Updates
  checkForUpdates: (customUrl?: string): Promise<UpdateCheckResult> => ipcRenderer.invoke('update:check', customUrl),
  getCurrentVersion: (): Promise<string> => ipcRenderer.invoke('update:getVersion'),
  applyUpdate: (): Promise<any> => ipcRenderer.invoke('update:apply'),
  restartApp: (): Promise<void> => ipcRenderer.invoke('app:restart'),

  // Window Controls
  windowMinimize: () => ipcRenderer.send('window:minimize'),
  windowMaximize: () => ipcRenderer.send('window:maximize'),
  windowClose: () => ipcRenderer.send('window:close'),
});
