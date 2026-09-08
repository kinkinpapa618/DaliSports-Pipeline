import { ChildProcessWithoutNullStreams, spawn, exec } from 'child_process';
import path from 'path';
import { PipelineLogMessage, PipelineOptions } from '../types';

export class PipelineProcessService {
  private activeProcess: ChildProcessWithoutNullStreams | null = null;
  private workspaceRoot: string;
  private onLogCallback: ((log: PipelineLogMessage) => void) | null = null;
  private onExitCallback: ((code: number | null) => void) | null = null;

  constructor(workspaceRoot: string) {
    this.workspaceRoot = workspaceRoot;
  }

  public isRunning(): boolean {
    return this.activeProcess !== null;
  }

  public setCallbacks(
    onLog: (log: PipelineLogMessage) => void,
    onExit: (code: number | null) => void
  ) {
    this.onLogCallback = onLog;
    this.onExitCallback = onExit;
  }

  public startPipeline(options: PipelineOptions): boolean {
    if (this.isRunning()) {
      this.emitLog('warn', 'Pipeline đang chạy! Vui lòng dừng tác vụ trước khi khởi chạy mới.');
      return false;
    }

    const scriptPath = path.join(this.workspaceRoot, 'system', 'auto_pipeline.py');
    const args: string[] = ['-u', scriptPath, options.tournamentPath];

    if (options.ytUrl && options.ytUrl.trim().length > 0) {
      args.push('--yt-url', options.ytUrl.trim());
    }
    if (options.courtName && options.courtName.trim().length > 0) {
      args.push('--court', options.courtName.trim());
    }
    if (options.tournamentName && options.tournamentName.trim().length > 0) {
      args.push('--tournament', options.tournamentName.trim());
    }
    if (options.sponsor && options.sponsor.trim().length > 0) {
      args.push('--sponsor', options.sponsor.trim());
    }
    if (options.category && options.category.trim().length > 0) {
      args.push('--category', options.category.trim());
    }
    if (options.skipCut) {
      args.push('--skip-cut');
    }
    if (options.dryRun) {
      args.push('--dry-run');
    }
    if (options.ytMode) {
      args.push('--yt-mode', options.ytMode);
    }

    this.emitLog('info', `[LAUNCH] Khởi chạy DaliSports Pipeline: python ${args.join(' ')}`);

    try {
      this.activeProcess = spawn('python', args, {
        cwd: this.workspaceRoot,
        env: {
          ...process.env,
          PYTHONIOENCODING: 'utf-8',
          PYTHONUNBUFFERED: '1',
        },
      });

      this.activeProcess.stdout.on('data', (data: Buffer) => {
        const text = data.toString('utf-8');
        this.processOutputLines(text, 'info');
      });

      this.activeProcess.stderr.on('data', (data: Buffer) => {
        const text = data.toString('utf-8');
        this.processOutputLines(text, 'warn');
      });

      this.activeProcess.on('close', (code: number | null) => {
        const exitMsg = code === 0 
          ? `[SUCCESS] Pipeline hoàn tất thành công (Exit Code: ${code})`
          : `[EXIT] Pipeline kết thúc với mã lỗi (Exit Code: ${code})`;
        this.emitLog(code === 0 ? 'success' : 'error', exitMsg);
        this.activeProcess = null;
        if (this.onExitCallback) {
          this.onExitCallback(code);
        }
      });

      this.activeProcess.on('error', (err: Error) => {
        this.emitLog('error', `[PROCESS ERROR] Không thể khởi động Python process: ${err.message}`);
        this.activeProcess = null;
        if (this.onExitCallback) {
          this.onExitCallback(-1);
        }
      });

      return true;
    } catch (err: any) {
      this.emitLog('error', `[EXCEPTION] Lỗi khi spawn process: ${err.message}`);
      return false;
    }
  }

  public killPipeline(): void {
    if (!this.activeProcess) {
      return;
    }

    const pid = this.activeProcess.pid;
    this.emitLog('warn', `[TERMINATE] Đang gửi tín hiệu dừng khẩn cấp cho PID: ${pid}...`);

    if (process.platform === 'win32' && pid) {
      exec(`taskkill /pid ${pid} /T /F`, (err) => {
        if (err) {
          this.emitLog('error', `Không thể taskkill PID ${pid}: ${err.message}`);
        } else {
          this.emitLog('warn', `Đã buộc dừng tiến trình PID ${pid} thành công.`);
        }
        this.activeProcess = null;
        if (this.onExitCallback) {
          this.onExitCallback(-999);
        }
      });
    } else {
      this.activeProcess.kill('SIGTERM');
      this.activeProcess = null;
    }
  }

  private processOutputLines(chunk: string, defaultLevel: 'info' | 'warn' | 'error' | 'success') {
    const lines = chunk.split(/\r?\n/);
    for (const line of lines) {
      if (!line.trim()) continue;
      let level = defaultLevel;
      const lower = line.toLowerCase();
      if (lower.includes('error') || lower.includes('thất bại') || lower.includes('traceback') || lower.includes('fail')) {
        level = 'error';
      } else if (lower.includes('success') || lower.includes('thành công') || lower.includes('hoàn tất') || lower.includes('done')) {
        level = 'success';
      } else if (lower.includes('warn') || lower.includes('cảnh báo') || lower.includes('skip')) {
        level = 'warn';
      }
      this.emitLog(level, line);
    }
  }

  private emitLog(level: 'info' | 'warn' | 'error' | 'success', message: string) {
    if (this.onLogCallback) {
      this.onLogCallback({
        id: Math.random().toString(36).substring(2, 9),
        timestamp: new Date().toLocaleTimeString('vi-VN', { hour12: false }),
        level,
        message,
      });
    }
  }
}
