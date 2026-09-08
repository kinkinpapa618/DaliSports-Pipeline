# test_pipeline_units.py - Unit and integration tests for DaliSports-Pipeline
import os
import sys
import tempfile
import unittest

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestNormalize(unittest.TestCase):
    def test_normalize_title(self):
        import normalize
        raw = "GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết | Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành"
        norm = normalize.normalize(raw)
        self.assertLessEqual(len(norm), 100)
        self.assertIn("THỦY MOCHI", norm)
        self.assertIn("Thắng - Minh vs Kai - Thành", norm)

    def test_normalize_timeline_line(self):
        import normalize
        line = "01:32:10 - 01:46:15 - GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026 | Đôi Hỗn Hợp 4.4 | Bán Kết 1 | Mạnh Thắng / Tuấn Minh vs Hưng Kai / Trịnh Tiến Thành"
        res = normalize.process_line(line)
        self.assertTrue(res.startswith("01:32:10 - 01:46:15 | "))
        title_part = res.split(" | ", 1)[1]
        self.assertLessEqual(len(title_part), 100)

class TestSeoHelper(unittest.TestCase):
    def test_sport_detection(self):
        import seo_helper
        self.assertEqual(seo_helper.detect_sport("Giải pickleball Thủy Mochi"), "pickleball")
        self.assertEqual(seo_helper.detect_sport("Giải cầu lông Hồng Loan"), "badminton")

    def test_slugify(self):
        import seo_helper
        slug = seo_helper.slugify("Giải Cầu Lông Hồng Loan Mở Rộng Năm 2026")
        self.assertEqual(slug, "giai-cau-long-hong-loan-mo-rong-nam-2026")

    def test_load_seo_config(self):
        import seo_helper
        cfg_pb = seo_helper.load_seo_config("GIẢI PICKLEBALL THỦY MOCHI LẦN 1 NĂM 2026")
        self.assertEqual(cfg_pb.get("sport"), "pickleball")
        self.assertIn("THỦY MOCHI", cfg_pb.get("tournament_full", ""))

        cfg_bl = seo_helper.load_seo_config("GIẢI CẦU LÔNG HỒNG LOAN MỞ RỘNG NĂM 2026")
        self.assertEqual(cfg_bl.get("sport"), "badminton")

class TestCutClipsHelpers(unittest.TestCase):
    def test_to_sec(self):
        import cut_clips
        self.assertEqual(cut_clips.to_sec("00:01:30"), 90)
        self.assertEqual(cut_clips.to_sec("01:00:00"), 3600)
        self.assertEqual(cut_clips.to_sec("15:30"), 930)

    def test_sanitize(self):
        import cut_clips
        name = 'GIẢI CAU LONG | Chung Kết <Đôi Nam>: A vs B?'
        clean = cut_clips.sanitize(name)
        for char in '<>:"/\\|?*':
            self.assertNotIn(char, clean)

class TestUploadSourceYoutubeChapters(unittest.TestCase):
    def test_build_chapters_and_title(self):
        import upload_source_youtube
        # Create a mock norms file
        with tempfile.NamedTemporaryFile(mode="w", suffix="_norms.txt", encoding="utf-8", delete=False) as tf:
            tf.write("00:05:00 - 00:25:00 | GIẢI CẦU LÔNG TEST 2026 | Đôi Nam | Văn A - Văn B vs Văn C - Văn D\n")
            tf.write("00:30:00 - 00:55:00 | GIẢI CẦU LÔNG TEST 2026 | Đôi Nữ | Thị E - Thị F vs Thị G - Thị H\n")
            temp_path = tf.name

        try:
            title, desc = upload_source_youtube.build_youtube_chapters_and_title(
                video_path="dummy_video.mp4",
                norms_path=temp_path,
                sport="badminton"
            )
            self.assertTrue(len(title) > 0)
            self.assertIn("00:05:00 Trận 01:", desc)
            self.assertIn("00:30:00 Trận 02:", desc)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == "__main__":
    unittest.main()
