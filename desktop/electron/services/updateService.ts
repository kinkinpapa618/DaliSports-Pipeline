import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { UpdateCheckResult, ApplyUpdateResult } from '../types';

const DEFAULT_UPDATE_URL = 'https://raw.githubusercontent.com/kinkinpapa618/DaliSports-Pipeline/main/version.json';

export class UpdateService {
  private workspaceRoot: string;
  private currentVersion: string;

  constructor(workspaceRoot: string) {
    this.workspaceRoot = workspaceRoot;
    this.currentVersion = this.readAppVersion();
  }

  private readAppVersion(): string {
    try {
      const pkgPath = path.join(this.workspaceRoot, 'desktop', 'package.json');
      if (fs.existsSync(pkgPath)) {
        const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
        if (pkg && pkg.version) return pkg.version;
      }
      const rootPkg = path.join(this.workspaceRoot, 'package.json');
      if (fs.existsSync(rootPkg)) {
        const pkg = JSON.parse(fs.readFileSync(rootPkg, 'utf-8'));
        if (pkg && pkg.version) return pkg.version;
      }
    } catch (e) {
      console.warn('[UpdateService] Error reading package.json version:', e);
    }
    return '1.1.0';
  }

  public getCurrentVersion(): string {
    return this.currentVersion;
  }

  /**
   * Compares two semantic version strings (e.g. "1.1.0" vs "1.0.0")
   * Returns:
   *   1 if v1 > v2
   *  -1 if v1 < v2
   *   0 if v1 === v2
   */
  public compareVersions(v1: string, v2: string): number {
    const clean1 = (v1 || '').replace(/^v/i, '').trim();
    const clean2 = (v2 || '').replace(/^v/i, '').trim();

    const parts1 = clean1.split('.').map((p) => parseInt(p, 10) || 0);
    const parts2 = clean2.split('.').map((p) => parseInt(p, 10) || 0);

    const maxLen = Math.max(parts1.length, parts2.length);
    for (let i = 0; i < maxLen; i++) {
      const p1 = parts1[i] ?? 0;
      const p2 = parts2[i] ?? 0;
      if (p1 > p2) return 1;
      if (p1 < p2) return -1;
    }
    return 0;
  }

  /**
   * Check for updates against remote URL or fallback to local manifest
   */
  public async checkForUpdates(customUrl?: string): Promise<UpdateCheckResult> {
    const checkedAt = new Date().toISOString();
    let manifestData: any = null;
    let fetchError: string | undefined = undefined;

    // Check custom URL or default URL
    const targetUrl = customUrl?.trim() || process.env.UPDATE_CHECK_URL?.trim() || DEFAULT_UPDATE_URL;

    if (targetUrl && (targetUrl.startsWith('http://') || targetUrl.startsWith('https://'))) {
      try {
        console.log(`[UpdateService] Fetching update manifest from: ${targetUrl}`);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 6000);

        const response = await fetch(targetUrl, {
          signal: controller.signal,
          headers: {
            'User-Agent': `DaliSportsStudio/${this.currentVersion}`,
            'Accept': 'application/json',
          },
        });
        clearTimeout(timeoutId);

        if (response.ok) {
          manifestData = await response.json();
        } else {
          fetchError = `Server trả về mã lỗi HTTP: ${response.status}`;
        }
      } catch (err: any) {
        console.warn('[UpdateService] Network fetch failed, will check local manifest:', err?.message || err);
        fetchError = err?.message || 'Lỗi kết nối mạng';
      }
    }

    // Fallback to local version.json if network fetch was not possible or returned no manifest
    if (!manifestData) {
      try {
        const localManifestPath = path.join(this.workspaceRoot, 'version.json');
        if (fs.existsSync(localManifestPath)) {
          console.log(`[UpdateService] Loading manifest from local file: ${localManifestPath}`);
          const raw = fs.readFileSync(localManifestPath, 'utf-8');
          manifestData = JSON.parse(raw);
        }
      } catch (err: any) {
        console.warn('[UpdateService] Failed reading local version.json:', err);
      }
    }

    // If still no manifest, return error result
    if (!manifestData || !manifestData.version) {
      return {
        hasUpdate: false,
        currentVersion: this.currentVersion,
        latestVersion: this.currentVersion,
        checkedAt,
        error: fetchError || 'Không tìm thấy thông tin phiên bản mới trên máy chủ.',
      };
    }

    const latestVersion = manifestData.version;
    const isNewer = this.compareVersions(latestVersion, this.currentVersion) > 0;

    return {
      hasUpdate: isNewer,
      currentVersion: this.currentVersion,
      latestVersion,
      title: manifestData.title || `Bản cập nhật v${latestVersion}`,
      releaseDate: manifestData.releaseDate,
      releaseNotes: Array.isArray(manifestData.releaseNotes) ? manifestData.releaseNotes : [],
      downloadUrl: manifestData.downloadUrl,
      changelogUrl: manifestData.changelogUrl,
      packageSize: manifestData.packageSize,
      mandatory: Boolean(manifestData.mandatory),
      checkedAt,
    };
  }

  /**
   * Automatically apply update via git pull or package sync
   */
  public async applyUpdate(): Promise<ApplyUpdateResult> {
    const logs: string[] = [];

    try {
      logs.push('[1/3] Đang kéo mã nguồn mới nhất từ GitHub...');
      await new Promise<void>((resolve, reject) => {
        exec('git pull origin main', { cwd: this.workspaceRoot }, (error, stdout, stderr) => {
          if (error) {
            logs.push(`Lỗi git pull: ${stderr || error.message}`);
            return reject(new Error(stderr || error.message));
          }
          if (stdout) logs.push(stdout.trim());
          resolve();
        });
      });

      logs.push('[2/3] Đang giải phóng cờ chặn bảo mật Windows SmartScreen...');
      try {
        await new Promise<void>((resolve) => {
          exec('powershell -Command "Get-ChildItem -Path \'*\' -Recurse -ErrorAction SilentlyContinue | Unblock-File"', { cwd: this.workspaceRoot }, () => resolve());
        });
      } catch (err: any) {
        logs.push(`Cảnh báo unblock: ${err?.message || err}`);
      }

      // Sync desktop/package.json with version.json if version.json has newer version
      try {
        const localVerJsonPath = path.join(this.workspaceRoot, 'version.json');
        const pkgPath = path.join(this.workspaceRoot, 'desktop', 'package.json');
        if (fs.existsSync(localVerJsonPath) && fs.existsSync(pkgPath)) {
          const vJson = JSON.parse(fs.readFileSync(localVerJsonPath, 'utf-8'));
          const pJson = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
          if (vJson.version && this.compareVersions(vJson.version, pJson.version) > 0) {
            pJson.version = vJson.version;
            fs.writeFileSync(pkgPath, JSON.stringify(pJson, null, 2), 'utf-8');
            logs.push(`Đã đồng bộ phiên bản package.json lên v${vJson.version}.`);
          }
        }
      } catch (syncErr: any) {
        console.warn('[UpdateService] Version sync error:', syncErr);
      }

      logs.push('[3/3] Đang cập nhật gói và biên dịch phiên bản mới...');
      const desktopDir = path.join(this.workspaceRoot, 'desktop');
      await new Promise<void>((resolve) => {
        exec('npm run build', { cwd: desktopDir }, (error, stdout) => {
          if (error) {
            logs.push(`Cảnh báo build: ${error.message}`);
          } else if (stdout) {
            logs.push('Biên dịch gói ứng dụng thành công.');
          }
          resolve();
        });
      });

      // Reload version in memory
      this.currentVersion = this.readAppVersion();

      return {
        success: true,
        message: `Đã cập nhật DaliSports Studio thành công! Vui lòng khởi động lại để áp dụng.`,
        logs,
      };
    } catch (err: any) {
      return {
        success: false,
        message: `Không thể hoàn tất cập nhật tự động: ${err?.message || err}`,
        logs,
      };
    }
  }
}

