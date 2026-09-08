import { SeoPreviewResult } from '../types';

export class SeoService {
  public generatePreview(params: {
    tournamentName?: string;
    sport?: string;
    round?: string;
    category?: string;
    playerA?: string;
    playerB?: string;
    court?: string;
    sponsor?: string;
    score?: string;
  }): SeoPreviewResult {
    const tournament = params.tournamentName || 'GIẢI CẦU LÔNG MỞ RỘNG 2026';
    const round = params.round || 'Chung Kết';
    const category = params.category || 'Đôi Nam';
    const playerA = params.playerA || 'Nguyễn Văn A / Trần Văn B';
    const playerB = params.playerB || 'Lê Văn C / Phạm Văn D';
    const score = params.score ? ` | Tỷ số: ${params.score}` : '';
    const court = params.court ? ` - ${params.court}` : '';

    const title = `[${round.toUpperCase()}] ${playerA} vs ${playerB} | ${category} - ${tournament}`;

    const description = `🏸 TRỰC TIẾP & HIGHLIGHTS: ${tournament}
🏆 Trận: ${playerA} VS ${playerB}
📌 Vòng thi đấu: ${round} | Nội dung: ${category}${court}${score}
${params.sponsor ? `✨ Nhà tài trợ chính: ${params.sponsor}\n` : ''}
🔥 Hãy Like, Chia sẻ & Đăng ký kênh DaliSports để không bỏ lỡ các pha cầu đỉnh cao và giải đấu hấp dẫn nhất!
-----------------------
#DaliSports #${params.sport || 'CauLong'} #${category.replace(/\s+/g, '')} #BadmintonHighlights #TheThao`;

    const tags = [
      'DaliSports',
      'Cầu Lông',
      'Badminton',
      'Pickleball',
      tournament,
      round,
      category,
      playerA,
      playerB,
      'Highlights cầu lông',
      'Trực tiếp thể thao'
    ];

    return {
      title,
      description,
      tags,
    };
  }
}
