import { app, BrowserWindow, ipcMain, shell } from 'electron';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { spawn, ChildProcessWithoutNullStreams } from 'child_process';

// Prevent GPU shader disk cache lock issues on Windows
app.commandLine.appendSwitch('disable-gpu-shader-disk-cache');

import { TournamentService } from './services/tournamentService';
import { TimelineService } from './services/timelineService';
import { PipelineProcessService } from './services/pipelineProcessService';
import { SeoService } from './services/seoService';
import { ConfigService } from './services/configService';
import { UpdateService } from './services/updateService';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Resolve project root (e:\www\DaliSports-Pipeline)
function getWorkspaceRoot(): string {
  // 1. If running from electron-builder portable executable
  if (process.env.PORTABLE_EXECUTABLE_DIR) {
    const pDir = process.env.PORTABLE_EXECUTABLE_DIR;
    if (fs.existsSync(path.join(pDir, 'system', 'auto_pipeline.py'))) return pDir;
    const p1 = path.resolve(pDir, '..');
    if (fs.existsSync(path.join(p1, 'system', 'auto_pipeline.py'))) return p1;
    const p2 = path.resolve(pDir, '../..');
    if (fs.existsSync(path.join(p2, 'system', 'auto_pipeline.py'))) return p2;
  }

  // 2. Check current working directory and parent paths
  const cur = process.cwd();
  if (fs.existsSync(path.join(cur, 'system', 'auto_pipeline.py'))) return cur;
  const parent = path.resolve(cur, '..');
  if (fs.existsSync(path.join(parent, 'system', 'auto_pipeline.py'))) return parent;
  const parent2 = path.resolve(cur, '../..');
  if (fs.existsSync(path.join(parent2, 'system', 'auto_pipeline.py'))) return parent2;

  // 3. Search up from __dirname
  let dirCheck = __dirname;
  for (let i = 0; i < 5; i++) {
    if (fs.existsSync(path.join(dirCheck, 'system', 'auto_pipeline.py'))) return dirCheck;
    dirCheck = path.resolve(dirCheck, '..');
  }

  // 4. Fallback to default workspace
  const defaultDir = 'E:\\www\\DaliSports-Pipeline';
  if (fs.existsSync(defaultDir)) return defaultDir;

  return cur;
}

const WORKSPACE_ROOT = getWorkspaceRoot();
console.log('[DaliSports Studio] Workspace Root:', WORKSPACE_ROOT);

const tournamentService = new TournamentService(WORKSPACE_ROOT);
const timelineService = new TimelineService();
const pipelineService = new PipelineProcessService(WORKSPACE_ROOT);
const seoService = new SeoService();
const configService = new ConfigService(WORKSPACE_ROOT);
const updateService = new UpdateService(WORKSPACE_ROOT);

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  const preloadCjs = path.join(__dirname, 'preload.cjs');
  const preloadJs = path.join(__dirname, 'preload.js');
  const preloadPath = fs.existsSync(preloadCjs) ? preloadCjs : preloadJs;
  console.log('[DaliSports Studio] Using Preload path:', preloadPath);

  const iconPath = path.join(WORKSPACE_ROOT, 'desktop', 'public', 'icon.png');

  mainWindow = new BrowserWindow({
    width: 1380,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    frame: false,
    backgroundColor: '#0b0f19',
    show: false,
    icon: fs.existsSync(iconPath) ? iconPath : undefined,
    webPreferences: {
      preload: preloadPath,
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: false,
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Connect pipeline service logs to renderer
  pipelineService.setCallbacks(
    (log) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('pipeline:log', log);
      }
    },
    (code) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('pipeline:exit', code);
      }
    }
  );

  // Load Vite Dev Server in dev, or dist/index.html in production
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

// IPC Registration
function registerIpcHandlers() {
  // Tournaments
  ipcMain.handle('tournaments:scan', async () => {
    return tournamentService.scanTournaments();
  });

  ipcMain.handle('tournaments:create', async (_, date: string, slug: string) => {
    return tournamentService.createTournament(date, slug);
  });

  ipcMain.handle('tournaments:update', async (_, tournamentPath: string, updates: any) => {
    return tournamentService.updateTournament(tournamentPath, updates);
  });

  ipcMain.handle('video:extractInfo', async (_, url: string) => {
    return tournamentService.extractVideoInfo(url);
  });

  ipcMain.handle('tournaments:createFromVideo', async (_, data: any) => {
    return tournamentService.createTournamentFromVideo(data);
  });

  // System
  ipcMain.handle('system:openFolder', async (_, dirPath: string) => {
    if (fs.existsSync(dirPath)) {
      shell.openPath(dirPath);
    }
  });

  ipcMain.handle('system:openUrl', async (_, url: string) => {
    if (url) {
      shell.openExternal(url);
    }
  });

  // Timeline
  ipcMain.handle('timeline:get', async (_, tournamentPath: string) => {
    return timelineService.getTimeline(tournamentPath);
  });

  ipcMain.handle('timeline:save', async (_, tournamentPath: string, matches: any[]) => {
    return timelineService.saveTimeline(tournamentPath, matches);
  });

  // Pipeline Execution
  ipcMain.handle('pipeline:start', async (_, options: any) => {
    return pipelineService.startPipeline(options);
  });

  ipcMain.handle('pipeline:kill', async () => {
    pipelineService.killPipeline();
  });

  ipcMain.handle('pipeline:isRunning', async () => {
    return pipelineService.isRunning();
  });

  // SEO Preview
  ipcMain.handle('seo:preview', async (_, params: any) => {
    return seoService.generatePreview(params);
  });

  // Config (.env)
  ipcMain.handle('config:get', async () => {
    return configService.getConfig();
  });

  ipcMain.handle('config:save', async (_, updates: any) => {
    return configService.saveConfig(updates);
  });

  // Updates
  ipcMain.handle('update:check', async (_, customUrl?: string) => {
    return updateService.checkForUpdates(customUrl);
  });

  ipcMain.handle('update:getVersion', async () => {
    return updateService.getCurrentVersion();
  });

  ipcMain.handle('update:apply', async () => {
    return updateService.applyUpdate();
  });

  ipcMain.handle('app:restart', async () => {
    app.relaunch();
    app.exit(0);
  });

  // Remote Tunnel Access
  let remoteServerProc: ChildProcessWithoutNullStreams | null = null;
  let remoteTunnelUrl: string | null = null;
  let remoteTunnelError: string | null = null;

  const stopRemoteServer = () => {
    if (remoteServerProc) {
      try {
        remoteServerProc.kill();
      } catch {}
      remoteServerProc = null;
    }
    remoteTunnelUrl = null;
    remoteTunnelError = null;
  };

  ipcMain.handle('tunnel:status', async () => {
    return {
      active: Boolean(remoteServerProc && remoteTunnelUrl),
      url: remoteTunnelUrl,
      error: remoteTunnelError,
    };
  });

  ipcMain.handle('tunnel:start', async () => {
    if (remoteServerProc && remoteTunnelUrl) {
      return { success: true, url: remoteTunnelUrl };
    }

    stopRemoteServer();

    const serverScript = path.join(WORKSPACE_ROOT, 'system', 'remote_server.py');
    return new Promise((resolve) => {
      try {
        remoteServerProc = spawn('python', ['-u', serverScript, '--tunnel', '--port', '8000'], {
          cwd: WORKSPACE_ROOT,
          env: {
            ...process.env,
            PYTHONIOENCODING: 'utf-8',
            PYTHONUNBUFFERED: '1',
          },
        });

        let resolved = false;

        const handleOutput = (data: Buffer) => {
          const text = data.toString('utf-8');
          const match = text.match(/https:\/\/[a-zA-Z0-9-]+\.trycloudflare\.com/);
          if (match && !resolved) {
            resolved = true;
            remoteTunnelUrl = match[0];
            remoteTunnelError = null;
            resolve({ success: true, url: remoteTunnelUrl });
          }
        };

        remoteServerProc.stdout.on('data', handleOutput);
        remoteServerProc.stderr.on('data', handleOutput);

        remoteServerProc.on('close', (code) => {
          remoteServerProc = null;
          remoteTunnelUrl = null;
          if (!resolved) {
            resolved = true;
            resolve({ success: false, error: `Máy chủ từ xa kết thúc (code ${code})` });
          }
        });

        remoteServerProc.on('error', (err) => {
          remoteTunnelError = err.message;
          if (!resolved) {
            resolved = true;
            resolve({ success: false, error: err.message });
          }
        });

        setTimeout(() => {
          if (!resolved) {
            resolved = true;
            resolve({
              success: Boolean(remoteTunnelUrl),
              url: remoteTunnelUrl,
              error: remoteTunnelUrl ? undefined : 'Quá thời gian kết nối Cloudflare Tunnel (15s)',
            });
          }
        }, 15000);
      } catch (err: any) {
        resolve({ success: false, error: err.message });
      }
    });
  });

  ipcMain.handle('tunnel:stop', async () => {
    stopRemoteServer();
    return { success: true };
  });

  // Window Controls
  ipcMain.on('window:minimize', () => {
    mainWindow?.minimize();
  });

  ipcMain.on('window:maximize', () => {
    if (mainWindow?.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow?.maximize();
    }
  });

  ipcMain.on('window:close', () => {
    stopRemoteServer();
    mainWindow?.close();
  });
}

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  console.log('[DaliSports Studio] Another instance is already running. Quitting duplicate...');
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(() => {
    registerIpcHandlers();
    createWindow();

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
      }
    });
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });
}
