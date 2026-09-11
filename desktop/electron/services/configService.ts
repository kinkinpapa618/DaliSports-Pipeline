import fs from 'fs';
import path from 'path';
import { EnvConfig } from '../types';

export class ConfigService {
  private workspaceRoot: string;
  private envPath: string;

  constructor(workspaceRoot: string) {
    this.workspaceRoot = workspaceRoot;
    this.envPath = path.join(workspaceRoot, '.env');
  }

  public getConfig(): EnvConfig {
    const config: EnvConfig = {
      GEMINI_API_KEY: '',
      GEMINI_MODEL: 'gemini-2.5-flash-lite',
      FB_PAGE_ID: '',
      FB_PAGE_ACCESS_TOKEN: '',
      UPDATE_CHECK_URL: '',
      VMIX_EXE_PATH: 'C:\\Program Files (x86)\\vMix\\vMix64.exe',
      FACEBOOK_PAGE_URL: 'https://www.facebook.com/dalisportss',
      VMIX_API_PORT: '8088',
      hasCookiesTxt: fs.existsSync(path.join(this.workspaceRoot, 'cookies.txt')),
      hasClientSecrets: fs.existsSync(path.join(this.workspaceRoot, 'client_secrets.json')),
      hasYoutubeToken: fs.existsSync(path.join(this.workspaceRoot, 'yt_profile', 'upload_youtube_oauth.json')),
    };

    if (fs.existsSync(this.envPath)) {
      try {
        const content = fs.readFileSync(this.envPath, 'utf-8');
        const lines = content.split(/\r?\n/);
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith('#')) continue;
          const eqIdx = trimmed.indexOf('=');
          if (eqIdx !== -1) {
            const key = trimmed.substring(0, eqIdx).trim();
            const val = trimmed.substring(eqIdx + 1).trim();
            if (key === 'GEMINI_API_KEY') config.GEMINI_API_KEY = val;
            else if (key === 'GEMINI_MODEL') config.GEMINI_MODEL = val;
            else if (key === 'FB_PAGE_ID') config.FB_PAGE_ID = val;
            else if (key === 'FB_PAGE_ACCESS_TOKEN') config.FB_PAGE_ACCESS_TOKEN = val;
            else if (key === 'YOUTUBE_CLIENT_SECRETS_FILE') config.YOUTUBE_CLIENT_SECRETS_FILE = val;
            else if (key === 'UPDATE_CHECK_URL') config.UPDATE_CHECK_URL = val;
            else if (key === 'VMIX_EXE_PATH') config.VMIX_EXE_PATH = val;
            else if (key === 'FACEBOOK_PAGE_URL') config.FACEBOOK_PAGE_URL = val;
            else if (key === 'VMIX_API_PORT') config.VMIX_API_PORT = val;
          }
        }
      } catch (err) {
        console.error('Lỗi khi đọc file .env:', err);
      }
    }

    return config;
  }

  public saveConfig(updates: Partial<EnvConfig>): boolean {
    try {
      let content = '';
      if (fs.existsSync(this.envPath)) {
        content = fs.readFileSync(this.envPath, 'utf-8');
      }

      const lines = content ? content.split(/\r?\n/) : [];
      const updatedKeys = new Set<string>();

      const targetUpdates: Record<string, string | undefined> = {
        GEMINI_API_KEY: updates.GEMINI_API_KEY,
        GEMINI_MODEL: updates.GEMINI_MODEL,
        FB_PAGE_ID: updates.FB_PAGE_ID,
        FB_PAGE_ACCESS_TOKEN: updates.FB_PAGE_ACCESS_TOKEN,
        UPDATE_CHECK_URL: updates.UPDATE_CHECK_URL,
        VMIX_EXE_PATH: updates.VMIX_EXE_PATH,
        FACEBOOK_PAGE_URL: updates.FACEBOOK_PAGE_URL,
        VMIX_API_PORT: updates.VMIX_API_PORT,
      };

      const newLines: string[] = [];
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#') && trimmed.includes('=')) {
          const eqIdx = trimmed.indexOf('=');
          const key = trimmed.substring(0, eqIdx).trim();
          if (key in targetUpdates && targetUpdates[key] !== undefined) {
            newLines.push(`${key}=${targetUpdates[key]}`);
            updatedKeys.add(key);
            continue;
          }
        }
        newLines.push(line);
      }

      // Append any keys that weren't in the original file
      for (const [k, v] of Object.entries(targetUpdates)) {
        if (v !== undefined && !updatedKeys.has(k)) {
          newLines.push(`${k}=${v}`);
        }
      }

      fs.writeFileSync(this.envPath, newLines.join('\n'), 'utf-8');
      return true;
    } catch (err) {
      console.error('Lỗi khi lưu file .env:', err);
      return false;
    }
  }
}
