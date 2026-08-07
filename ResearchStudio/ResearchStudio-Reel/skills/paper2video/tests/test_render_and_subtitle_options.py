from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = SKILL_DIR / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"paper2video_test_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


add_subtitles = load_script("add_subtitles")
render_video = load_script("render_video")


class FocusStyleTests(unittest.TestCase):
    def test_focus_box_and_laser_is_a_supported_production_combination(self) -> None:
        self.assertIn("box_laser", render_video.VALID_HIGHLIGHT_STYLES)
        self.assertIn("box_laser", render_video.LASER_STYLES)
        self.assertNotIn("box_laser", render_video.SPOTLIGHT_STYLES)


class SubtitleBarTests(unittest.TestCase):
    def test_bar_geometry_preserves_aspect_ratio_and_output_frame(self) -> None:
        content_w, content_h, x, actual_bar = add_subtitles.subtitle_bar_geometry(
            1920, 1080, 173,
        )
        self.assertEqual((content_w, content_h), (1610, 906))
        self.assertEqual(x, 155)
        self.assertEqual(actual_bar, 174)
        self.assertAlmostEqual(content_w / content_h, 16 / 9, places=2)

    def test_ass_places_white_caption_inside_reserved_bar(self) -> None:
        cue = add_subtitles.Cue(
            index=1,
            start=0.5,
            end=2.5,
            text="A caption that must not cover the slide.",
        )
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bar.ass"
            add_subtitles.write_ass(
                [cue],
                path,
                video_w=1280,
                video_h=720,
                font_name="DejaVu Sans",
                font_size=44,
                outline_width=2.0,
                shadow_depth=0.5,
                subtitle_box=False,
                subtitle_bar=True,
                subtitle_bar_height=116,
                box_opacity=0.62,
                box_padding=10.0,
            )
            text = path.read_text(encoding="utf-8")
        self.assertIn("PlayResX: 1280", text)
        self.assertIn("PlayResY: 720", text)
        self.assertIn(",1,0.0,0.0,2,40,40,39,1", text)
        self.assertIn(r"{\c&H00FFFFFF&}", text)


class SubtitleDisabledTests(unittest.TestCase):
    def test_caption_free_delivery_stream_copies_video_audio_only(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "raw.mp4"
            output = Path(tmp) / "video.mp4"
            source.touch()
            with patch.object(add_subtitles.subprocess, "run") as run:
                run.return_value.returncode = 0
                add_subtitles.copy_without_subtitles(source, output, "ffmpeg")

        command = run.call_args.args[0]
        self.assertIn("-c", command)
        self.assertEqual(command[command.index("-c") + 1], "copy")
        self.assertIn("-sn", command)
        self.assertIn("-dn", command)
        self.assertIn("0:v:0", command)
        self.assertIn("0:a?", command)


if __name__ == "__main__":
    unittest.main()
