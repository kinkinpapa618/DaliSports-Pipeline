const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // Tournaments
  scanTournaments: () => ipcRenderer.invoke('tournaments:scan'),
  createTournament: (date, slug) => ipcRenderer.invoke('tournaments:create', date, slug),
  createTournamentFull: (payload) => ipcRenderer.invoke('tournaments:createFull', payload),
  updateTournament: (tournamentPath, updates) => ipcRenderer.invoke('tournaments:update', tournamentPath, updates),
  extractVideoInfo: (url) => ipcRenderer.invoke('video:extractInfo', url),
  createTournamentFromVideo: (data) => ipcRenderer.invoke('tournaments:createFromVideo', data),
  buildVmixPreset: (tournamentPath) => ipcRenderer.invoke('livestream:buildPreset', tournamentPath),
  startLive: (tournamentPath) => ipcRenderer.invoke('livestream:startLive', tournamentPath),
  syncDaliSports: () => ipcRenderer.invoke('tournaments:syncDaliSports'),
  importBackdrop: (tournamentPath) => ipcRenderer.invoke('livestream:importBackdrop', tournamentPath),
  importLogos: (tournamentPath) => ipcRenderer.invoke('livestream:importLogos', tournamentPath),
  importTvc: (tournamentPath) => ipcRenderer.invoke('livestream:importTvc', tournamentPath),
  importAthletes: (tournamentPath) => ipcRenderer.invoke('livestream:importAthletes', tournamentPath),
  openFolder: (dirPath) => ipcRenderer.invoke('system:openFolder', dirPath),
  openUrl: (url) => ipcRenderer.invoke('system:openUrl', url),

  // Timeline
  getTimeline: (tournamentPath) => ipcRenderer.invoke('timeline:get', tournamentPath),
  saveTimeline: (tournamentPath, matches) => ipcRenderer.invoke('timeline:save', tournamentPath, matches),

  // Pipeline
  startPipeline: (options) => ipcRenderer.invoke('pipeline:start', options),
  killPipeline: () => ipcRenderer.invoke('pipeline:kill'),
  isPipelineRunning: () => ipcRenderer.invoke('pipeline:isRunning'),
  onPipelineLog: (callback) => {
    ipcRenderer.on('pipeline:log', (_, log) => callback(log));
  },
  onPipelineExit: (callback) => {
    ipcRenderer.on('pipeline:exit', (_, code) => callback(code));
  },

  // SEO Preview
  getSeoPreview: (params) => ipcRenderer.invoke('seo:preview', params),

  // Config (.env)
  getConfig: () => ipcRenderer.invoke('config:get'),
  saveConfig: (updates) => ipcRenderer.invoke('config:save', updates),

  // Updates
  checkForUpdates: (customUrl) => ipcRenderer.invoke('update:check', customUrl),
  getCurrentVersion: () => ipcRenderer.invoke('update:getVersion'),
  applyUpdate: () => ipcRenderer.invoke('update:apply'),
  restartApp: () => ipcRenderer.invoke('app:restart'),

  // Remote Tunnel Access
  getTunnelStatus: () => ipcRenderer.invoke('tunnel:status'),
  startTunnel: () => ipcRenderer.invoke('tunnel:start'),
  stopTunnel: () => ipcRenderer.invoke('tunnel:stop'),

  // Window Controls
  windowMinimize: () => ipcRenderer.send('window:minimize'),
  windowMaximize: () => ipcRenderer.send('window:maximize'),
  windowClose: () => ipcRenderer.send('window:close'),
});
