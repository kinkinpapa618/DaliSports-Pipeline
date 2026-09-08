import fs from 'fs';
import path from 'path';
import { MatchTimelineItem } from '../types';

export class TimelineService {
  public getTimeline(tournamentPath: string): { matches: MatchTimelineItem[]; rawJson?: any; detectedFile?: string } {
    const timeRegex = /^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)/;
    const rootTimelineJson = path.join(tournamentPath, 'timeline.json');

    // 1. If root timeline.json exists and has matches, use it
    if (fs.existsSync(rootTimelineJson)) {
      try {
        const content = fs.readFileSync(rootTimelineJson, 'utf-8');
        const parsed = JSON.parse(content);
        const norm = this.normalizeMatches(parsed);
        if (norm.length > 0) {
          return { matches: norm, rawJson: parsed, detectedFile: 'timeline.json' };
        }
      } catch (err) {
        console.error('Failed to read timeline.json:', err);
      }
    }

    try {
      if (!fs.existsSync(tournamentPath)) {
        return { matches: [] };
      }

      const rootEntries = fs.readdirSync(tournamentPath, { withFileTypes: true });

      // 2. Priority: Other .json in root (e.g. *timeline*.json, raw_ocr_*.json)
      for (const entry of rootEntries) {
        if (!entry.isFile() || entry.name === 'timeline.json') continue;
        const name = entry.name.toLowerCase();
        if (name.endsWith('.json') && (name.includes('timeline') || name.includes('matches') || name.includes('raw_ocr'))) {
          try {
            const content = fs.readFileSync(path.join(tournamentPath, entry.name), 'utf-8');
            const parsed = JSON.parse(content);
            const norm = this.normalizeMatches(parsed);
            if (norm.length > 0) {
              // Cache to timeline.json if not present
              if (!fs.existsSync(rootTimelineJson)) {
                this.saveTimeline(tournamentPath, norm);
              }
              return { matches: norm, rawJson: parsed, detectedFile: entry.name };
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

      txtCandidates.sort((a, b) => {
        const aNorms = a.includes('norms') ? -1 : 1;
        const bNorms = b.includes('norms') ? -1 : 1;
        return aNorms - bNorms;
      });

      for (const txtName of txtCandidates) {
        try {
          const txtPath = path.join(tournamentPath, txtName);
          const content = fs.readFileSync(txtPath, 'utf-8');
          const parsedMatches = this.parseTextTimeline(content);
          if (parsedMatches.length > 0) {
            // Automatically save to timeline.json for easy editing
            if (!fs.existsSync(rootTimelineJson)) {
              this.saveTimeline(tournamentPath, parsedMatches);
            }
            return { matches: parsedMatches, rawJson: { source: txtName, matches: parsedMatches }, detectedFile: txtName };
          }
        } catch (err) {
          console.error(`Lỗi khi đọc file text timeline ${txtName}:`, err);
        }
      }

      // 4. Check 1 level of subdirectories (e.g. chung-ket-chieu-30-8/source_timeline.txt)
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
              const relPath = path.join(entry.name, subFile);
              if (lower.endsWith('.json')) {
                try {
                  const content = fs.readFileSync(fullSubPath, 'utf-8');
                  const parsed = JSON.parse(content);
                  const norm = this.normalizeMatches(parsed);
                  if (norm.length > 0) {
                    if (!fs.existsSync(rootTimelineJson)) {
                      this.saveTimeline(tournamentPath, norm);
                    }
                    return { matches: norm, rawJson: parsed, detectedFile: relPath };
                  }
                } catch {}
              } else {
                const content = fs.readFileSync(fullSubPath, 'utf-8');
                const parsedMatches = this.parseTextTimeline(content);
                if (parsedMatches.length > 0) {
                  if (!fs.existsSync(rootTimelineJson)) {
                    this.saveTimeline(tournamentPath, parsedMatches);
                  }
                  return { matches: parsedMatches, rawJson: { source: relPath, matches: parsedMatches }, detectedFile: relPath };
                }
              }
            }
          }
        } catch {}
      }
    } catch (err) {
      console.error('Failed to search timeline files:', err);
    }

    return { matches: [] };
  }

  public parseTextTimeline(content: string): MatchTimelineItem[] {
    const lines = content.split(/\r?\n/);
    const matches: MatchTimelineItem[] = [];
    const timeRegex = /^\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*-\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*[-|:]?\s*(.*)$/;

    let matchId = 1;
    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line || line.startsWith('#')) continue;

      const match = line.match(timeRegex);
      if (!match) continue;

      let startTime = match[1];
      let endTime = match[2];
      if (startTime.length === 5) startTime = `00:${startTime}`;
      if (endTime.length === 5) endTime = `00:${endTime}`;
      const rest = match[3].trim();

      const segments = rest.split('|').map(s => s.trim()).filter(Boolean);

      let tournamentName = '';
      let category = 'Nội dung chung';
      let round = 'Vòng đấu';
      let playerA = 'Đội A';
      let playerB = 'Đội B';

      for (let i = 0; i < segments.length; i++) {
        const seg = segments[i];
        if (/giai|giải/i.test(seg) && !tournamentName) {
          tournamentName = seg;
        } else if (/bán kết|chung kết|tứ kết|vòng bảng|bk|ck|tk|final|semi|tranh/i.test(seg) && round === 'Vòng đấu') {
          round = seg;
        } else if ((/vs/i.test(seg) || (seg.includes('-') && !seg.toLowerCase().includes('u1') && !seg.toLowerCase().includes('đôi') && !seg.toLowerCase().includes('nhóm'))) && (playerA === 'Đội A' || /vs/i.test(seg))) {
          const vsSplit = seg.split(/\s+vs\s+|\s+VS\s+/);
          if (vsSplit.length >= 2) {
            playerA = vsSplit[0].trim();
            playerB = vsSplit[1].trim();
          } else {
            const dashSplit = seg.split(/\s+-\s+/);
            if (dashSplit.length >= 2) {
              playerA = dashSplit[0].trim();
              playerB = dashSplit[1].trim();
            } else {
              playerA = seg;
            }
          }
        } else if (!/giai|giải/i.test(seg) && category === 'Nội dung chung') {
          category = seg;
        }
      }

      if (playerA === 'Đội A' && playerB === 'Đội B') {
        const vsMatch = rest.match(/([^\-|]+?)\s+vs\s+([^\-|]+)/i);
        if (vsMatch) {
          playerA = vsMatch[1].trim();
          playerB = vsMatch[2].trim();
        }
      }

      matches.push({
        match_id: matchId++,
        court: 'Sân 1',
        round: round || 'Vòng Đấu',
        category: category || 'Trận Đấu',
        player_a: playerA,
        player_b: playerB,
        start_time: startTime,
        end_time: endTime,
        selected: true,
      });
    }

    return matches;
  }

  public saveTimeline(tournamentPath: string, matches: MatchTimelineItem[]): boolean {
    const timelinePath = path.join(tournamentPath, 'timeline.json');

    try {
      // Backup if exists
      if (fs.existsSync(timelinePath)) {
        const backupPath = path.join(tournamentPath, 'timeline.json.bak');
        fs.copyFileSync(timelinePath, backupPath);
      }

      // Write formatted
      const dataToSave = {
        generated_at: new Date().toISOString(),
        total_matches: matches.length,
        matches: matches
      };

      fs.writeFileSync(timelinePath, JSON.stringify(dataToSave, null, 2), 'utf-8');
      return true;
    } catch (err) {
      console.error('Failed to save timeline.json:', err);
      return false;
    }
  }

  private normalizeMatches(raw: any): MatchTimelineItem[] {
    let list: any[] = [];
    if (Array.isArray(raw)) {
      list = raw;
    } else if (raw && Array.isArray(raw.matches)) {
      list = raw.matches;
    } else if (raw && typeof raw === 'object') {
      // If matches are stored as key-value
      list = Object.values(raw);
    }

    return list.map((item, idx) => ({
      match_id: item.match_id ?? idx + 1,
      court: item.court ?? 'Sân 1',
      round: item.round ?? 'Vòng Bảng',
      category: item.category ?? 'Đôi Nam',
      player_a: item.player_a ?? item.team_a ?? 'Đội A',
      player_b: item.player_b ?? item.team_b ?? 'Đội B',
      start_time: item.start_time ?? '00:00:00',
      end_time: item.end_time ?? '00:00:00',
      scores: item.scores ?? {
        set1: item.score_set1 ?? '',
        set2: item.score_set2 ?? '',
        set3: item.score_set3 ?? '',
      },
      score: item.score ?? (item.scores ? `${item.scores.set1 || ''} ${item.scores.set2 || ''}`.trim() : ''),
      winner: item.winner ?? '',
      selected: item.selected !== false,
      ...item
    }));
  }
}
