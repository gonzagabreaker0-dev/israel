"""End-to-end tests on synthetic footage generated with FFmpeg. Run: python -m unittest discover -s tests -v"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vew import edit, importer, qc, subtitles  # noqa: E402
from vew.presets import PRESETS, get_preset  # noqa: E402
from vew.probe import summarize  # noqa: E402
from vew.project import Project  # noqa: E402
from vew.util import VewError, sha256  # noqa: E402

SRT = """1
00:00:00,500 --> 00:00:02,000
Hello from the workstation

2
00:00:02,200 --> 00:00:04,000
Fresh coffee, made {right}
"""


def synth(path, w, h, fps, dur, audio=True, pattern="testsrc2"):
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"{pattern}=s={w}x{h}:r={fps}:d={dur}"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=44100:d={dur}", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(cmd, check=True)


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="vew_test_"))
        cls.a, cls.b, cls.c = cls.tmp / "a.mp4", cls.tmp / "b.mov", cls.tmp / "c.mkv"
        synth(cls.a, 1280, 720, 30, 4)
        synth(cls.b, 720, 1280, 25, 3)
        synth(cls.c, 640, 360, 24, 2, audio=False)
        cls.srt = cls.tmp / "t.srt"
        cls.srt.write_text(SRT, encoding="utf-8")
        cls.hashes = {p: sha256(p) for p in (cls.a, cls.b, cls.c)}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def out(self, name):
        return self.tmp / "out" / name

    def test_01_probe(self):
        i = summarize(self.a)
        self.assertEqual((i["width"], i["height"]), (1280, 720))
        self.assertAlmostEqual(i["fps"], 30, places=1)
        self.assertTrue(i["has_audio"])
        self.assertFalse(summarize(self.c)["has_audio"])

    def test_02_trim(self):
        r = edit.trim(self.a, self.out("trim.mp4"), 1.0, 3.0)
        i = summarize(r["out"])
        self.assertAlmostEqual(i["duration"], 2.0, delta=0.15)
        self.assertEqual((i["width"], i["height"]), (1280, 720))
        self.assertTrue(i["has_audio"])

    def test_03_merge_mixed_sources(self):
        r = edit.merge([self.a, self.b, self.c], self.out("merge.mp4"), get_preset("instagram_reels"), quality="preview")
        i = summarize(r["out"])
        self.assertEqual((i["width"], i["height"]), (1080, 1920))
        self.assertAlmostEqual(i["duration"], 9.0, delta=0.3)
        self.assertTrue(i["has_audio"])  # silent clip got synthesized silence

    def test_04_export_all_presets_no_stretch(self):
        for name, p in PRESETS.items():
            r = edit.export(self.a, self.out(f"exp_{name}.mp4"), get_preset(name, 0.25), quality="preview")
            i = summarize(r["out"])
            self.assertEqual((i["width"], i["height"]), (get_preset(name, 0.25)["w"], get_preset(name, 0.25)["h"]), name)
            self.assertAlmostEqual(i["fps"], p["fps"], places=1)

    def test_05_subtitle_burn_and_wording_preserved(self):
        r = subtitles.burn_subtitles(self.a, self.out("sub.mp4"), self.srt, "highlight", get_preset("youtube"),
                                     keywords=["coffee"], quality="preview")
        ass = Path(r["ass"]).read_text(encoding="utf-8")
        self.assertIn("Hello from the workstation", ass)
        self.assertIn("{\\c&H0000D4FF}coffee", ass)  # keyword highlighted with accent colour
        self.assertIn("\\{right\\}", ass)  # literal braces escaped, wording unchanged
        self.assertTrue(Path(r["out"]).stat().st_size > 0)
        # captions actually changed pixels vs the un-captioned export
        plain = edit.export(self.a, self.out("plain.mp4"), {**get_preset("youtube"), "w": 1280, "h": 720}, quality="preview")
        def frame_hash(p):
            return subprocess.run(["ffmpeg", "-v", "error", "-ss", "1", "-i", str(p), "-frames:v", "1", "-f", "md5", "-"],
                                  capture_output=True, text=True).stdout
        self.assertNotEqual(frame_hash(r["out"]), frame_hash(plain["out"]))

    def test_06_srt_roundtrip_and_corrections(self):
        cues = subtitles.parse_srt(self.srt)
        self.assertEqual(len(cues), 2)
        n = subtitles.apply_corrections(self.srt, {"workstation": "work station"}, self.out("fix.srt"))
        self.assertEqual(n, 1)
        self.assertIn("work station", self.out("fix.srt").read_text(encoding="utf-8"))

    def test_07_source_protection_and_no_overwrite(self):
        with self.assertRaises(VewError):
            edit.trim(self.a, self.a, 0, 1)
        edit.trim(self.a, self.out("once.mp4"), 0, 1, quality="preview")
        with self.assertRaises(VewError):
            edit.trim(self.a, self.out("once.mp4"), 0, 1, quality="preview")
        for p, h in self.hashes.items():
            self.assertEqual(sha256(p), h, f"{p.name} was modified")

    def test_08_import_analyze_build_final_qc(self):
        pr = Project.create(self.tmp / "projects", "Test Ad")
        e = importer.import_video(self.a, pr)
        importer.import_video(self.b, pr)
        rep = json.loads(Path(e["analysis"]).read_text())
        self.assertEqual(rep["width"], 1280)
        self.assertTrue(Path(rep["audio_wav"]).exists())
        self.assertEqual(len(rep["thumbnails"]), 3)
        with self.assertRaises(VewError):
            importer.import_video(self.tmp / "t.srt", pr)  # unsupported type
        shutil.copy(self.srt, pr.path("subs") / "t.srt")
        cfg = pr.config
        cfg.update(preset="instagram_reels", clips=[
            {"src": "source/a.mp4", "start": 0.5, "end": 3.5},
            {"src": "source/b.mov", "start": 0, "end": 2.0, "mode": "crop"}],
            subtitles={"srt": "subs/t.srt", "style": "animated", "keywords": ["coffee"]})
        pr.save_config(cfg)
        prev = pr.build("preview")
        self.assertTrue(prev["passed"], prev["checks"])
        fin = pr.build("final")
        self.assertTrue(fin["passed"], fin["checks"])
        fin2 = pr.build("final")  # second final must NOT overwrite the first
        self.assertNotEqual(fin["output"], fin2["output"])
        self.assertTrue(Path(fin["output"]).exists())
        i = summarize(fin["output"])
        self.assertEqual((i["width"], i["height"]), (1080, 1920))
        self.assertAlmostEqual(i["duration"], 5.0, delta=0.3)
        self.assertTrue((pr.path("logs") / "render.log.jsonl").stat().st_size > 0)
        self.assertTrue(list(pr.path("reports").glob("*.md")))
        # source copy is read-only and unchanged
        self.assertEqual(sha256(pr.path("source") / "a.mp4"), self.hashes[self.a])

    def test_09_qc_detects_problems(self):
        r = edit.export(self.a, self.out("qc_src.mp4"), get_preset("youtube", 0.5), quality="preview")
        rep = qc.run_qc(r["out"], get_preset("youtube", 0.5), expected_duration=10.0)
        self.assertFalse(rep["passed"])
        self.assertEqual({c["name"]: c["status"] for c in rep["checks"]}["duration"], "fail")
        rep = qc.run_qc(r["out"], get_preset("tiktok", 0.5), expected_duration=4.0)
        self.assertEqual({c["name"]: c["status"] for c in rep["checks"]}["resolution"], "fail")
        rep = qc.run_qc(r["out"], get_preset("youtube", 0.5), 4.0, assets=["/nonexistent.mp4"])
        self.assertEqual({c["name"]: c["status"] for c in rep["checks"]}["assets"], "fail")

    def test_10_speed_and_scene_detect(self):
        r = edit.render_sequence([{"src": self.a, "start": 0, "end": 4, "speed": 2.0}], self.out("fast.mp4"),
                                 640, 360, 30, "pad", "preview")
        self.assertAlmostEqual(summarize(r["out"])["duration"], 2.0, delta=0.2)
        joined = self.out("joined.mp4")
        edit.merge([self.a, self.b], joined, get_preset("youtube", 0.25), quality="preview")
        self.assertTrue(importer.detect_scenes(joined, 0.3), "hard cut between different clips should be detected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
