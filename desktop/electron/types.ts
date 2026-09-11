export interface MatchTimelineItem {
  match_id?: number | string;
  court?: string;
  round?: string;
  category?: string;
  player_a?: string;
  player_b?: string;
  start_time: string | number; // e.g. "00:15:30" or 930
  end_time: string | number;   // e.g. "00:45:10" or 2710
  scores?: {
    set1?: string;
    set2?: string;
    set3?: string;
  };
  score?: string;
  winner?: string;
  raw_text?: string;
  selected?: boolean;
  [key: string]: any;
}

export interface TournamentInfo {
  id: string;
  name: string;
  folderName: string;
  path: string;
  date: string;
  sportType: 'badminton' | 'pickleball' | 'tennis' | 'other';
  sourceUrl?: string;
  court?: string;
  category?: string;
  sponsor?: string;
  description?: string;
  hasVideo: boolean;
  videoFile?: string;
  videoSizeMb?: number;
  hasTimeline: boolean;
  timelineFile?: string;
  matchCount: number;
  hasClips: boolean;
  clipCount: number;
  uploadedYoutube: boolean;
  uploadedFacebook: boolean;
  // Livestream fields
  hasPresetVmix?: boolean;
  hasBackdrop?: boolean;
  backdropPath?: string;
  hasLogos?: boolean;
  logosCount?: number;
  hasTvc?: boolean;
  tvcCount?: number;
  hasAthletesList?: boolean;
  hasDieule?: boolean;
  hasStartBat?: boolean;
}

export interface CreateTournamentPayload {
  name: string;
  sportType: 'badminton' | 'pickleball' | 'tennis' | 'other';
  date?: string;
  description?: string;
  court?: string;
  sponsor?: string;
}

export interface BuildVmixPresetResult {
  success: boolean;
  presetPath?: string;
  tournamentName?: string;
  sport?: string;
  hasBackdrop?: boolean;
  logosCount?: number;
  tvcCount?: number;
  error?: string;
}

export interface PipelineOptions {
  tournamentPath: string;
  ytUrl?: string;
  courtName?: string;
  tournamentName?: string;
  sponsor?: string;
  category?: string;
  // 4 bước có thể chạy tuần tự hoặc độc lập
  skipDownload?: boolean;
  skipTimeline?: boolean;
  skipNormalize?: boolean;
  skipCut?: boolean;
  skipUpload?: boolean;
  dryRun?: boolean;
  // Platform & mode
  platform?: 'youtube' | 'facebook' | 'both';
  ytMode?: 'source' | 'clips' | 'both';
  enableFb?: boolean;
  enableYt?: boolean;
}

export interface PipelineLogMessage {
  id: string;
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

export interface SeoPreviewResult {
  title: string;
  description: string;
  tags: string[];
}

export interface EnvConfig {
  GEMINI_API_KEY: string;
  GEMINI_MODEL: string;
  FB_PAGE_ID: string;
  FB_PAGE_ACCESS_TOKEN: string;
  YOUTUBE_CLIENT_SECRETS_FILE?: string;
  UPDATE_CHECK_URL?: string;
  VMIX_EXE_PATH?: string;
  FACEBOOK_PAGE_URL?: string;
  VMIX_API_PORT?: string;
  hasCookiesTxt: boolean;
  hasClientSecrets: boolean;
  hasYoutubeToken: boolean;
}

export interface UpdateCheckResult {
  hasUpdate: boolean;
  currentVersion: string;
  latestVersion: string;
  title?: string;
  releaseDate?: string;
  releaseNotes?: string[];
  downloadUrl?: string;
  changelogUrl?: string;
  packageSize?: string;
  mandatory?: boolean;
  checkedAt: string;
  error?: string;
}

export interface ApplyUpdateResult {
  success: boolean;
  message: string;
  logs?: string[];
}
