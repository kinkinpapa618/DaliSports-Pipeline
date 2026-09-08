import fs from 'fs';
import path from 'path';
import { execFile } from 'child_process';
import { TournamentInfo } from '../types';

export class TournamentService {
  private workspaceRoot: string;

  constructor(workspaceRoot: string) {
    this.workspaceRoot = workspaceRoot;
  }

  public scanTournaments(): TournamentInfo[] {
    const results: TournamentInfo[] = [];

    try {
      if (!fs.existsSync(this.workspaceRoot)) {
        return results;
      }

      const entries = fs.readdirSync(this.workspaceRoot, { withFileTypes: true });

      // Pattern: YYYY-MM-DD_slug
      const tournamentDirRegex = /^\d{4}-\d{2}-\d{2}_.+$/;

      for (const entry of entries) {
        if (!entry.isDirectory()) continue;
        if (!tournamentDirRegex.test(entry.name)) continue;

        const folderName = entry.name;
        const tournamentPath = path.join(this.workspaceRoot, folderName);
        const dateMatch = folderName.match(/^(\d{4}-\d{2}-\d{2})/);
        const date = dateMatch ? dateMatch[1] : '';

        let name = folderName.substring(11).replace(/[-_]/g, ' ');
        name = name.charAt(0).toUpperCase() + name.slice(1);

        let sportType: 'badminton' | 'pickleball' | 'tennis' | 'other' = 'badminton';
        const lowerFolder = folderName.toLowerCase();
        if (lowerFolder.includes('pickleball')) {
          sportType = 'pickleball';
        } else if (lowerFolder.includes('tennis')) {
          sportType = 'tennis';
        }

        let sourceUrl: string | undefined;
        let court: string | undefined;
        let category: string | undefined;
        let sponsor: string | undefined;
        const infoFile = path.join(tournamentPath, 'tournament_info.json');
        if (fs.existsSync(infoFile)) {
          try {
            const info = JSON.parse(fs.readFileSync(infoFile, 'utf-8'));
            if (info.name) name = info.name;
            if (info.sportType) sportType = info.sportType;
            if (info.source_url) sourceUrl = info.source_url;
            if (info.court) court = info.court;
            if (info.category) category = info.category;
            if (info.sponsor) sponsor = info.sponsor;
          } catch {}
        }

        // Check video
        const videoDir = path.join(tournamentPath, 'video');
        let hasVideo = false;
        let videoFile: string | undefined;
        let videoSizeMb: number | undefined;

        if (fs.existsSync(videoDir)) {
          const files = fs.readdirSync(videoDir);
          const videoMatch = files.find(f => /\.(mp4|mkv|mov|ts|avi)$/i.test(f));
          if (videoMatch) {
            hasVideo = true;
            videoFile = path.join('video', videoMatch);
            try {
              const stat = fs.statSync(path.join(videoDir, videoMatch));
              videoSizeMb = Math.round(stat.size / (1024 * 1024));
            } catch {}
          }
        }

        // Smart auto-detect timeline (.json, .txt, norms, in root or subdirectories)
        const tlInfo = this.detectTournamentTimeline(tournamentPath);
        const hasTimeline = tlInfo.hasTimeline;
        const timelineFile = tlInfo.timelineFile;
        const matchCount = tlInfo.matchCount;

        // Check clips
        const clipsDir = path.join(tournamentPath, 'clips');
        let hasClips = false;
        let clipCount = 0;

        if (fs.existsSync(clipsDir)) {
          const clipFiles = fs.readdirSync(clipsDir).filter(f => f.endsWith('.mp4'));
          clipCount = clipFiles.length;
          hasClips = clipCount > 0;
        }

        // Check upload status
        const rootUploadLog = path.join(this.workspaceRoot, 'upload_source_log.txt');
        const tournamentUploadLog = path.join(tournamentPath, 'upload_source_log.txt');
        let uploadedYoutube = false;
        let uploadedFacebook = false;

        const checkLogs = (filePath: string) => {
          if (fs.existsSync(filePath)) {
            try {
              const content = fs.readFileSync(filePath, 'utf-8');
              if (content.includes(folderName) || content.includes('http')) {
                uploadedYoutube = true;
              }
            } catch {}
          }
        };

        checkLogs(rootUploadLog);
        checkLogs(tournamentUploadLog);

        const fbLog = path.join(tournamentPath, 'upload_fb_log.txt');
        if (fs.existsSync(fbLog)) {
          uploadedFacebook = true;
        }

        results.push({
          id: folderName,
          name,
          folderName,
          path: tournamentPath,
          date,
          sportType,
          sourceUrl,
          court,
          category,
          sponsor,
          hasVideo,
          videoFile,
          videoSizeMb,
          hasTimeline,
          timelineFile: hasTimeline ? 'timeline.json' : undefined,
          matchCount,
          hasClips,
          clipCount,
          uploadedYoutube,
          uploadedFacebook,
        });
      }

      // Sort by date descending
      results.sort((a, b) => b.date.localeCompare(a.date));
    } catch (err) {
      console.error('Error scanning tournaments:', err);
    }

    return results;
  }

  public createTournament(dateStr: string, slug: string): { success: boolean; folderName: string; path: string; error?: string } {
    try {
      // 1. Remove leading date if user typed YYYY-MM-DD_ in slug
      let cleanSlug = slug.trim().replace(/^\d{4}-\d{2}-\d{2}[_-]/, '');

      // 2. Remove Vietnamese diacritics
      cleanSlug = cleanSlug
        .replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, 'a')
        .replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, 'e')
        .replace(/ì|í|ị|ỉ|ĩ/g, 'i')
        .replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, 'o')
        .replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, 'u')
        .replace(/ỳ|ý|ỵ|ỷ|ỹ/g, 'y')
        .replace(/đ/g, 'd')
        .replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, 'A')
        .replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, 'E')
        .replace(/Ì|Í|Ị|Ỉ|Ĩ/g, 'I')
        .replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, 'O')
        .replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, 'U')
        .replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, 'Y')
        .replace(/Đ/g, 'D');

      // 3. Format to clean lowercase hyphen-separated slug
      let formattedSlug = cleanSlug.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
      if (!formattedSlug) {
        formattedSlug = 'giai-dau-the-thao';
      }

      if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
        dateStr = new Date().toISOString().split('T')[0];
      }

      const folderName = `${dateStr}_${formattedSlug}`;
      if (!fs.existsSync(this.workspaceRoot)) {
        fs.mkdirSync(this.workspaceRoot, { recursive: true });
      }
      const targetDir = path.join(this.workspaceRoot, folderName);

      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }
      fs.mkdirSync(path.join(targetDir, 'video'), { recursive: true });
      fs.mkdirSync(path.join(targetDir, 'clips'), { recursive: true });
      fs.mkdirSync(path.join(targetDir, 'thumbnails'), { recursive: true });

      // Create initial timeline.json so Timeline tab can detect it immediately
      const initialTimelinePath = path.join(targetDir, 'timeline.json');
      if (!fs.existsSync(initialTimelinePath)) {
        const initialData = {
          tournament_name: slug.replace(/[-_]/g, ' ').toUpperCase(),
          date: dateStr,
          generated_at: new Date().toISOString(),
          total_matches: 0,
          matches: [],
        };
        fs.writeFileSync(initialTimelinePath, JSON.stringify(initialData, null, 2), 'utf-8');
      }

      return { success: true, folderName, path: targetDir };
    } catch (err: any) {
      console.error('Lỗi tạo thư mục giải đấu:', err);
      return { success: false, folderName: '', path: '', error: err.message };
    }
  }

  public async extractVideoInfo(url: string): Promise<any> {
    const scriptPath = path.join(this.workspaceRoot, 'system', 'extract_video_info.py');
    return new Promise((resolve) => {
      execFile(
        'python',
        ['-u', scriptPath, url],
        {
          cwd: this.workspaceRoot,
          env: {
            ...process.env,
            PYTHONIOENCODING: 'utf-8',
            PYTHONUNBUFFERED: '1',
          },
          timeout: 25000,
        },
        (error, stdout, stderr) => {
          if (error) {
            console.warn('Lỗi khi extract video info qua script python:', error.message, stderr);
            // Heuristic fallback so it never blocks the user
            const cleanUrl = url.split('?')[0].replace(/\/+$/, '');
            const urlPart = path.basename(cleanUrl);
            const today = new Date().toISOString().split('T')[0];
            return resolve({
              success: true,
              url,
              raw_title: urlPart || 'Video Giải Đấu Thể Thao Mới',
              tournament_name: urlPart ? `Giải Đấu ${urlPart}` : 'Giải Đấu Thể Thao Mới',
              date: today,
              sport_type: 'badminton',
              court: 'Sân 1',
              category: 'Đôi Nam',
              round: 'Vòng Bảng',
              slug: 'giai-dau-the-thao-moi',
              folder_name: `${today}_giai-dau-the-thao-moi`,
              duration_seconds: 0,
            });
          }

          try {
            const data = JSON.parse(stdout.trim());
            resolve(data);
          } catch (parseErr) {
            console.error('Không parse được JSON từ extract_video_info.py:', stdout);
            resolve({
              success: false,
              error: 'Không đọc được dữ liệu phản hồi từ trình trích xuất.',
            });
          }
        }
      );
    });
  }

  public createTournamentFromVideo(data: {
    date: string;
    slug?: string;
    tournamentName: string;
    sportType?: 'badminton' | 'pickleball' | 'tennis' | 'other';
    url?: string;
    court?: string;
    category?: string;
    round?: string;
  }): { success: boolean; folderName: string; path: string; error?: string } {
    try {
      const dateStr = data.date && /^\d{4}-\d{2}-\d{2}$/.test(data.date)
        ? data.date
        : new Date().toISOString().split('T')[0];

      let rawSlug = data.slug || data.tournamentName;
      let cleanSlug = rawSlug.trim().replace(/^\d{4}-\d{2}-\d{2}[_-]/, '');
      cleanSlug = cleanSlug
        .replace(/à|á|ạ|ả|ã|â|ầ|ấ|ậ|ẩ|ẫ|ă|ằ|ắ|ặ|ẳ|ẵ/g, 'a')
        .replace(/è|é|ẹ|ẻ|ẽ|ê|ề|ế|ệ|ể|ễ/g, 'e')
        .replace(/ì|í|ị|ỉ|ĩ/g, 'i')
        .replace(/ò|ó|ọ|ỏ|õ|ô|ồ|ố|ộ|ổ|ỗ|ơ|ờ|ớ|ợ|ở|ỡ/g, 'o')
        .replace(/ù|ú|ụ|ủ|ũ|ư|ừ|ứ|ự|ử|ữ/g, 'u')
        .replace(/ỳ|ý|ỵ|ỷ|ỹ/g, 'y')
        .replace(/đ/g, 'd')
        .replace(/À|Á|Ạ|Ả|Ã|Â|Ầ|Ấ|Ậ|Ẩ|Ẫ|Ă|Ằ|Ắ|Ặ|Ẳ|Ẵ/g, 'A')
        .replace(/È|É|Ẹ|Ẻ|Ẽ|Ê|Ề|Ế|Ệ|Ể|Ễ/g, 'E')
        .replace(/Ì|Í|Ị|Ỉ|Ĩ/g, 'I')
        .replace(/Ò|Ó|Ọ|Ỏ|Õ|Ô|Ồ|Ố|Ộ|Ổ|Ỗ|Ơ|Ờ|Ớ|Ợ|Ở|Ỡ/g, 'O')
        .replace(/Ù|Ú|Ụ|Ủ|Ũ|Ư|Ừ|Ứ|Ự|Ử|Ữ/g, 'U')
        .replace(/Ỳ|Ý|Ỵ|Ỷ|Ỹ/g, 'Y')
        .replace(/Đ/g, 'D');

      let formattedSlug = cleanSlug.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
      if (!formattedSlug) {
        formattedSlug = 'giai-dau-the-thao';
      }

      const folderName = `${dateStr}_${formattedSlug}`;
      if (!fs.existsSync(this.workspaceRoot)) {
        fs.mkdirSync(this.workspaceRoot, { recursive: true });
      }
      const targetDir = path.join(this.workspaceRoot, folderName);

      if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
      }
      fs.mkdirSync(path.join(targetDir, 'video'), { recursive: true });
      fs.mkdirSync(path.join(targetDir, 'clips'), { recursive: true });
      fs.mkdirSync(path.join(targetDir, 'thumbnails'), { recursive: true });

      // Lưu metadata giải đấu vào tournament_info.json
      const infoFile = path.join(targetDir, 'tournament_info.json');
      const infoData = {
        name: data.tournamentName || formattedSlug.replace(/[-_]/g, ' ').toUpperCase(),
        date: dateStr,
        sportType: data.sportType || 'badminton',
        source_url: data.url || '',
        court: data.court || 'Sân 1',
        category: data.category || 'Đôi Nam',
        round: data.round || 'Vòng Bảng',
        created_at: new Date().toISOString(),
      };
      fs.writeFileSync(infoFile, JSON.stringify(infoData, null, 2), 'utf-8');

      // Tạo timeline.json ban đầu
      const initialTimelinePath = path.join(targetDir, 'timeline.json');
      if (!fs.existsSync(initialTimelinePath)) {
        const initialTimeline = {
          tournament_name: data.tournamentName ? data.tournamentName.toUpperCase() : formattedSlug.replace(/[-_]/g, ' ').toUpperCase(),
          date: dateStr,
          sport_type: data.sportType || 'badminton',
          source_url: data.url || '',
          generated_at: new Date().toISOString(),
          total_matches: 0,
          matches: [],
        };
        fs.writeFileSync(initialTimelinePath, JSON.stringify(initialTimeline, null, 2), 'utf-8');
      }

      return { success: true, folderName, path: targetDir };
    } catch (err: any) {
      console.error('Lỗi tạo giải đấu từ video:', err);
      return { success: false, folderName: '', path: '', error: err.message };
    }
  }

  public updateTournament(
    tournamentPath: string,
    updates: {
      name?: string;
      date?: string;
      sportType?: 'badminton' | 'pickleball' | 'tennis' | 'other';
      sourceUrl?: string;
      court?: string;
      category?: string;
      sponsor?: string;
    }
  ): { success: boolean; error?: string } {
    try {
      if (!fs.existsSync(tournamentPath)) {
        return { success: false, error: 'Thư mục giải đấu không tồn tại.' };
      }

      const infoFile = path.join(tournamentPath, 'tournament_info.json');
      let currentData: any = {};
      if (fs.existsSync(infoFile)) {
        try {
          currentData = JSON.parse(fs.readFileSync(infoFile, 'utf-8'));
        } catch {}
      }

      const updatedData = {
        ...currentData,
        name: updates.name !== undefined ? updates.name : currentData.name,
        date: updates.date !== undefined ? updates.date : currentData.date,
        sportType: updates.sportType !== undefined ? updates.sportType : currentData.sportType,
        source_url: updates.sourceUrl !== undefined ? updates.sourceUrl : currentData.source_url,
        court: updates.court !== undefined ? updates.court : currentData.court,
        category: updates.category !== undefined ? updates.category : currentData.category,
        sponsor: updates.sponsor !== undefined ? updates.sponsor : currentData.sponsor,
        updated_at: new Date().toISOString(),
      };

      fs.writeFileSync(infoFile, JSON.stringify(updatedData, null, 2), 'utf-8');

      // Đồng bộ thông tin giải vào timeline.json nếu có
      const timelinePath = path.join(tournamentPath, 'timeline.json');
      if (fs.existsSync(timelinePath)) {
        try {
          const tlContent = JSON.parse(fs.readFileSync(timelinePath, 'utf-8'));
          if (typeof tlContent === 'object' && !Array.isArray(tlContent)) {
            if (updates.name) tlContent.tournament_name = updates.name.toUpperCase();
            if (updates.date) tlContent.date = updates.date;
            if (updates.sportType) tlContent.sport_type = updates.sportType;
            if (updates.sourceUrl) tlContent.source_url = updates.sourceUrl;
            fs.writeFileSync(timelinePath, JSON.stringify(tlContent, null, 2), 'utf-8');
          }
        } catch {}
      }

      return { success: true };
    } catch (err: any) {
      console.error('Lỗi cập nhật thông tin giải đấu:', err);
      return { success: false, error: err.message };
    }
  }

  public detectTournamentTimeline(tournamentPath: string): { hasTimeline: boolean; timelineFile?: string; matchCount: number; fullPath?: string } {
    const timeRegex = /^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)/;

    // 1. Check root timeline.json
    const rootTimelineJson = path.join(tournamentPath, 'timeline.json');
    if (fs.existsSync(rootTimelineJson)) {
      try {
        const data = JSON.parse(fs.readFileSync(rootTimelineJson, 'utf-8'));
        const matches = Array.isArray(data) ? data : (Array.isArray(data.matches) ? data.matches : []);
        if (matches.length > 0) {
          return { hasTimeline: true, timelineFile: 'timeline.json', matchCount: matches.length, fullPath: rootTimelineJson };
        }
      } catch {}
    }

    try {
      if (!fs.existsSync(tournamentPath)) {
        return { hasTimeline: false, matchCount: 0 };
      }

      const rootEntries = fs.readdirSync(tournamentPath, { withFileTypes: true });

      // 2. Priority: Other .json in root (e.g. *timeline*.json, raw_ocr_*.json)
      for (const entry of rootEntries) {
        if (!entry.isFile()) continue;
        const name = entry.name.toLowerCase();
        if (name.endsWith('.json') && (name.includes('timeline') || name.includes('matches') || name.includes('raw_ocr'))) {
          try {
            const data = JSON.parse(fs.readFileSync(path.join(tournamentPath, entry.name), 'utf-8'));
            const matches = Array.isArray(data) ? data : (Array.isArray(data.matches) ? data.matches : []);
            if (matches.length > 0) {
              return { hasTimeline: true, timelineFile: entry.name, matchCount: matches.length, fullPath: path.join(tournamentPath, entry.name) };
            }
          } catch {}
        }
      }

      // 3. Priority: .txt files in root (*_timeline_norms.txt, timeline.txt, *_timeline.txt)
      const txtCandidates: string[] = [];
      for (const entry of rootEntries) {
        if (!entry.isFile()) continue;
        const name = entry.name.toLowerCase();
        if (name.endsWith('.txt') && (name.includes('timeline') || name.includes('norms'))) {
          txtCandidates.push(entry.name);
        }
      }

      // Sort so norms file is preferred over raw
      txtCandidates.sort((a, b) => {
        const aNorms = a.includes('norms') ? -1 : 1;
        const bNorms = b.includes('norms') ? -1 : 1;
        return aNorms - bNorms;
      });

      for (const txtName of txtCandidates) {
        try {
          const content = fs.readFileSync(path.join(tournamentPath, txtName), 'utf-8');
          const validLines = content.split(/\r?\n/).filter(l => timeRegex.test(l.trim()));
          if (validLines.length > 0) {
            return { hasTimeline: true, timelineFile: txtName, matchCount: validLines.length, fullPath: path.join(tournamentPath, txtName) };
          }
        } catch {}
      }

      // 4. Check 1 level of subdirectories (e.g. chung-ket-chieu-30-8/source_timeline.txt, doi-hon-hop-4-4/...)
      for (const entry of rootEntries) {
        if (!entry.isDirectory()) continue;
        const subName = entry.name.toLowerCase();
        if (subName === 'video' || subName === 'clips' || subName === 'thumbnails') continue;

        const subDirPath = path.join(tournamentPath, entry.name);
        try {
          const subFiles = fs.readdirSync(subDirPath);
          for (const subFile of subFiles) {
            const lower = subFile.toLowerCase();
            if ((lower.endsWith('.txt') || lower.endsWith('.json')) && (lower.includes('timeline') || lower.includes('norms'))) {
              const fullSubPath = path.join(subDirPath, subFile);
              if (lower.endsWith('.json')) {
                try {
                  const data = JSON.parse(fs.readFileSync(fullSubPath, 'utf-8'));
                  const matches = Array.isArray(data) ? data : (Array.isArray(data.matches) ? data.matches : []);
                  if (matches.length > 0) {
                    return { hasTimeline: true, timelineFile: path.join(entry.name, subFile), matchCount: matches.length, fullPath: fullSubPath };
                  }
                } catch {}
              } else {
                const content = fs.readFileSync(fullSubPath, 'utf-8');
                const validLines = content.split(/\r?\n/).filter(l => timeRegex.test(l.trim()));
                if (validLines.length > 0) {
                  return { hasTimeline: true, timelineFile: path.join(entry.name, subFile), matchCount: validLines.length, fullPath: fullSubPath };
                }
              }
            }
          }
        } catch {}
      }

      // 5. Fallback: if root timeline.json exists even with 0 matches
      if (fs.existsSync(rootTimelineJson)) {
        return { hasTimeline: true, timelineFile: 'timeline.json', matchCount: 0, fullPath: rootTimelineJson };
      }
    } catch (err) {
      console.error('Lỗi khi tự nhận biết timeline:', err);
    }

    return { hasTimeline: false, matchCount: 0 };
  }
}
