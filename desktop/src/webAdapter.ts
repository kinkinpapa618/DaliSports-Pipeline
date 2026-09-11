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
  public isWeb: boolean = true;
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

  async createTournamentFull(payload: any): Promise<{ success: boolean; folderName: string; path: string; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/tournaments/create-full`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await res.json();
  }

  async buildVmixPreset(tournamentPath: string): Promise<any> {
    const res = await fetch(`${this.getBaseUrl()}/api/livestream/build-preset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournamentPath }),
    });
    return await res.json();
  }

  async startLive(tournamentPath: string): Promise<{ success: boolean; error?: string }> {
    const res = await fetch(`${this.getBaseUrl()}/api/livestream/start-live`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournamentPath }),
    });
    return await res.json();
  }

  async syncDaliSports(): Promise<any> {
    const res = await fetch(`${this.getBaseUrl()}/api/tournaments/sync-dalisports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return await res.json();
  }

  async importBackdrop(tournamentPath: string): Promise<{ success: boolean; dest?: string; error?: string }> {
    return new Promise((resolve) => {
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.accept = 'image/png,image/jpeg,image/webp,image/bmp';
      inp.onchange = async () => {
        const file = inp.files?.[0];
        if (!file) return resolve({ success: false, error: 'Đã hủy chọn file' });
        const form = new FormData();
        form.append('file', file);
        try {
          const res = await fetch(`${this.getBaseUrl()}/api/livestream/import-backdrop?tournamentPath=${encodeURIComponent(tournamentPath)}`, {
            method: 'POST',
            body: form,
          });
          const data = await res.json();
          resolve(data);
        } catch (e: any) {
          resolve({ success: false, error: e.message });
        }
      };
      inp.click();
    });
  }

  async importLogos(tournamentPath: string): Promise<{ success: boolean; count?: number; error?: string }> {
    return new Promise((resolve) => {
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.multiple = true;
      inp.accept = 'image/png,image/jpeg,image/webp,image/svg+xml,image/bmp';
      inp.onchange = async () => {
        const files = inp.files;
        if (!files || files.length === 0) return resolve({ success: false, error: 'Đã hủy chọn file' });
        const form = new FormData();
        for (let i = 0; i < files.length; i++) {
          form.append('files', files[i]);
        }
        try {
          const res = await fetch(`${this.getBaseUrl()}/api/livestream/import-logos?tournamentPath=${encodeURIComponent(tournamentPath)}`, {
            method: 'POST',
            body: form,
          });
          const data = await res.json();
          resolve(data);
        } catch (e: any) {
          resolve({ success: false, error: e.message });
        }
      };
      inp.click();
    });
  }

  async importTvc(tournamentPath: string): Promise<{ success: boolean; count?: number; error?: string }> {
    return new Promise((resolve) => {
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.multiple = true;
      inp.accept = 'video/mp4,video/quicktime,video/x-matroska,video/avi,video/*,.mp4,.mov,.mkv,.ts';
      inp.onchange = async () => {
        const files = inp.files;
        if (!files || files.length === 0) return resolve({ success: false, error: 'Đã hủy chọn file' });
        const form = new FormData();
        for (let i = 0; i < files.length; i++) {
          form.append('files', files[i]);
        }
        try {
          const res = await fetch(`${this.getBaseUrl()}/api/livestream/import-tvc?tournamentPath=${encodeURIComponent(tournamentPath)}`, {
            method: 'POST',
            body: form,
          });
          const data = await res.json();
          resolve(data);
        } catch (e: any) {
          resolve({ success: false, error: e.message });
        }
      };
      inp.click();
    });
  }

  async importAthletes(tournamentPath: string): Promise<{ success: boolean; dest?: string; error?: string }> {
    return new Promise((resolve) => {
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.accept = '.csv,.xlsx,.xls,.txt,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
      inp.onchange = async () => {
        const file = inp.files?.[0];
        if (!file) return resolve({ success: false, error: 'Đã hủy chọn file' });
        const form = new FormData();
        form.append('file', file);
        try {
          const res = await fetch(`${this.getBaseUrl()}/api/livestream/import-athletes?tournamentPath=${encodeURIComponent(tournamentPath)}`, {
            method: 'POST',
            body: form,
          });
          const data = await res.json();
          resolve(data);
        } catch (e: any) {
          resolve({ success: false, error: e.message });
        }
      };
      inp.click();
    });
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

  // --- Timeline (độc lập: get / save / generate / normalize) ---
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

  async generateTimeline(tournamentPath: string): Promise<any> {
    const res = await fetch(`${this.getBaseUrl()}/api/timeline/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournamentPath }),
    });
    return await res.json();
  }

  async normalizeTimeline(tournamentPath: string): Promise<any> {
    const res = await fetch(`${this.getBaseUrl()}/api/timeline/normalize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tournamentPath }),
    });
    return await res.json();
  }

  async previewChapters(tournamentPath: string): Promise<{ title: string; description: string; chapters: string[] }> {
    const res = await fetch(`${this.getBaseUrl()}/api/chapters/preview?path=${encodeURIComponent(tournamentPath)}`);
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  }

  async importVideoFile(tournamentPath: string, file: File): Promise<any> {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${this.getBaseUrl()}/api/video/import?tournamentPath=${encodeURIComponent(tournamentPath)}`, {
      method: 'POST',
      body: form,
    });
    return await res.json();
  }

  // Electron-compatible import (file picker)
  async importVideoFileDialog(tournamentPath: string): Promise<any> {
    // Fallback: trigger hidden input for web mode
    return new Promise((resolve) => {
      const inp = document.createElement('input');
      inp.type = 'file';
      inp.accept = 'video/mp4,video/*,.mp4,.mkv,.mov,.avi,.ts';
      inp.onchange = async () => {
        const file = inp.files?.[0];
        if (!file) return resolve({ success: false });
        const r = await this.importVideoFile(tournamentPath, file);
        resolve(r);
      };
      inp.click();
    });
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
