/**
 * webAdapter.ts
 * Adapter allowing DaliSports Studio React frontend to seamlessly work in any standard
 * web browser when accessed remotely via Cloudflare Tunnel or local network IP.
 * Automatically polyfills `window.api` with REST HTTP calls and WebSocket log streaming.
 */

import {
  TournamentInfo,
  MatchTimelineItem,
  PipelineOptions,
  PipelineLogMessage,
  SeoPreviewResult,
  EnvConfig,
  UpdateCheckResult,
  ApplyUpdateResult,
} from './types';

class WebApiAdapter {
  private logListeners: ((log: PipelineLogMessage) => void)[] = [];
  private exitListeners: ((code: number | null) => void)[] = [];
  private ws: WebSocket | null = null;
  private wsReconnectTimer: any = null;

  constructor() {
    this.initWebSocket();
  }

  private getBaseUrl(): string {
    return window.location.origin;
  }

  private initWebSocket() {
    if (typeof window === 'undefined') return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/pipeline`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'log') {
            this.logListeners.forEach((cb) => cb(msg.payload));
          } else if (msg.type === 'exit') {
            this.exitListeners.forEach((cb) => cb(msg.payload));
          }
        } catch (e) {
          console.warn('[WebAdapter] WebSocket message parse error:', e);
        }
      };

      this.ws.onclose = () => {
        if (!this.wsReconnectTimer) {
          this.wsReconnectTimer = setTimeout(() => {
            this.wsReconnectTimer = null;
            this.initWebSocket();
          }, 3000);
        }
      };

      this.ws.onerror = () => {
        if (this.ws) this.ws.close();
      };
    } catch (err) {
      console.warn('[WebAdapter] WebSocket initialization error:', err);
    }
  }

  // --- Tournaments ---
  async scanTournaments(): Promise<TournamentInfo[]> {
    const res = await fetch(`${this.getBaseUrl()}/api/tournaments`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  }

  async createTournament(date: string, slug: string): Promise<{ success: boolean; folderName: string; path: string; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tournaments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ date, slug }),
    });
    return await res.json();
  }

  async updateTournament(tournamentPath: string, updates: any): Promise<{ success: boolean; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tournaments/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournamentPath, updates }),
    });
    return await res.json();
  }

  async extractVideoInfo(url: string): Promise<any> {
    const res = await fetch(`${this.getBaseUrl()}/api/video/extract-info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    return await res.json();
  }

  async createTournamentFromVideo(data: any): Promise<{ success: boolean; folderName: string; path: string; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tournaments/create-from-video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return await res.json();
  }

  // --- System ---
  async openFolder(dirPath: string): Promise<void> {
    await fetch(`${this.getBaseUrl()}/api/system/open-folder`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ dirPath }),
    });
  }

  async openUrl(url: string): Promise<void> {
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }

  // --- Timeline ---
  async getTimeline(tournamentPath: string): Promise<{ matches: MatchTimelineItem[]; rawJson?: any; detectedFile?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/timeline?path=${encodeURIComponent(tournamentPath)}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  }

  async saveTimeline(tournamentPath: string, matches: MatchTimelineItem[]): Promise<boolean> {
    const res = await fetch(`${this.getBaseUrl()}/api/timeline`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournamentPath, matches }),
    });
    const data = await res.json();
    return Boolean(data.success);
  }

  // --- Pipeline Execution ---
  async startPipeline(options: PipelineOptions): Promise<boolean> {
    const res = await fetch(`${this.getBaseUrl()}/api/pipeline/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(options),
    });
    const data = await res.json();
    return Boolean(data.success);
  }

  async killPipeline(): Promise<void> {
    await fetch(`${this.getBaseUrl()}/api/pipeline/kill`, { method: 'POST' });
  }

  async isPipelineRunning(): Promise<boolean> {
    const res = await fetch(`${this.getBaseUrl()}/api/pipeline/status`);
    const data = await res.json();
    return Boolean(data.isRunning);
  }

  onPipelineLog(callback: (log: PipelineLogMessage) => void): void {
    this.logListeners.push(callback);
  }

  onPipelineExit(callback: (code: number | null) => void): void {
    this.exitListeners.push(callback);
  }

  // --- SEO Preview ---
  async getSeoPreview(params: any): Promise<SeoPreviewResult> {
    const res = await fetch(`${this.getBaseUrl()}/api/seo/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return await res.json();
  }

  // --- Config (.env) ---
  async getConfig(): Promise<EnvConfig> {
    const res = await fetch(`${this.getBaseUrl()}/api/config`);
    return await res.json();
  }

  async saveConfig(updates: Partial<EnvConfig>): Promise<boolean> {
    const res = await fetch(`${this.getBaseUrl()}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates),
    });
    const data = await res.json();
    return Boolean(data.success);
  }

  // --- Tunnel Remote Access ---
  async getTunnelStatus(): Promise<{ active: boolean; url?: string; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tunnel/status`);
    return await res.json();
  }

  async startTunnel(): Promise<{ success: boolean; url?: string; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tunnel/start`, { method: 'POST' });
    return await res.json();
  }

  async stopTunnel(): Promise<{ success: boolean }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tunnel/stop`, { method: 'POST' });
    return await res.json();
  }

  // --- Updates ---
  async checkForUpdates(customUrl?: string): Promise<UpdateCheckResult> {
    const query = customUrl ? `?url=${encodeURIComponent(customUrl)}` : '';
    const res = await fetch(`${this.getBaseUrl()}/api/update/check${query}`);
    return await res.json();
  }

  async getCurrentVersion(): Promise<string> {
    const res = await fetch(`${this.getBaseUrl()}/api/version`);
    const data = await res.json();
    return data.version || '1.1.0';
  }

  async applyUpdate(): Promise<ApplyUpdateResult> {
    const res = await fetch(`${this.getBaseUrl()}/api/update/apply`, { method: 'POST' });
    return await res.json();
  }

  async restartApp(): Promise<void> {
    window.location.reload();
  }

  // --- Window Controls (Simulated for Web Browser) ---
  windowMinimize(): void {
    console.log('[WebAdapter] Minimize action triggered in browser mode');
  }

  windowMaximize(): void {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  windowClose(): void {
    if (window.confirm('Bạn có chắc chắn muốn đóng trang điều khiển từ xa?')) {
      window.close();
    }
  }
}

// Polyfill window.api if not in Electron desktop
if (typeof window !== 'undefined' && !window.api) {
  console.log('[DaliSports Studio] Initializing WebApiAdapter for Remote Browser Mode...');
  window.api = new WebApiAdapter() as any;
}
