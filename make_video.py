from argparse import ArgumentParser
import os
from pathlib import Path
import random
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from core import TextToVideoPipeline, VideoConfig
from core.xtts_paths import load_xtts_paths

AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}

def _resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()

def _read_payload(args) -> str:
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    if args.text:
        return args.text.strip()
    raise ValueError("Provide --text or --text-file")

def _parse_segmented_payload(payload: str) -> tuple[list[str], list[tuple[str, ...]]]:
    """
    Parses a script where each line is a pre-segmented sentence.
    Trusts user input verbatim. Supports <u>Keyword</u> for inline highlights.
    """
    segments: list[str] = []
    highlights: list[tuple[str, ...]] = []

    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # Extract keywords and clean tags
        keywords = re.findall(r"<u>(.*?)</u>", line)
        sentence = re.sub(r"<u>(.*?)</u>", r"\1", line)
        
        segments.append(sentence)
        highlights.append(tuple(keywords))

    if not segments:
        raise ValueError("No valid segments found. Provide one sentence per line.")

    return segments, highlights

def _pick_random_music(musics_dir: Path, seed: int | None) -> Path | None:
    if not musics_dir.exists() or not musics_dir.is_dir():
        return None
    music_files = [
        p for p in musics_dir.iterdir()
        if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS
    ]
    if not music_files:
        return None
    rng = random.Random(seed)
    return rng.choice(music_files)

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Generate video from pre-segmented sentences.")
    parser.add_argument("--text", type=str, help="Input script (one sentence per line).")
    parser.add_argument("--text-file", type=str, help="Path to script file.")
    parser.add_argument("--output", type=str, default="outputs/output.mp4", help="Output path.")
    parser.add_argument("--fonts-dir", type=str, default="materials/fonts")
    parser.add_argument("--musics-dir", type=str, default="musics")
    parser.add_argument("--no-bgm", action="store_true")
    parser.add_argument("--bgm-volume", type=float, default=0.18)
    parser.add_argument("--tts-gain", type=float, default=1.35)
    parser.add_argument("--voice", type=str, choices=["female", "male"], default="male")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    parser.add_argument("--threads", type=int, default=max(1, os.cpu_count() or 1))
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--xtts-config", type=str, default="xtts_config.json")
    parser.add_argument("--tts-device", type=str, default="auto")
    return parser

def main():
    parser = build_parser()
    args = parser.parse_args()

    payload = _read_payload(args)
    segments, highlights = _parse_segmented_payload(payload)

    config = VideoConfig(width=args.width, height=args.height, fps=args.fps)
    pipeline = TextToVideoPipeline.create(
        fonts_dir=PROJECT_ROOT / args.fonts_dir,
        config=config,
        seed=args.seed,
    )

    music_path = None if args.no_bgm else _pick_random_music(PROJECT_ROOT / args.musics_dir, args.seed)
    xtts_paths = load_xtts_paths(PROJECT_ROOT, _resolve_path(PROJECT_ROOT, args.xtts_config))
    xtts_speaker_wav = str(xtts_paths.resolve_speaker(args.voice))

    # Render
    output_path = pipeline.render(
        text="\n".join(segments),
        output_path=PROJECT_ROOT / args.output,
        threads=args.threads,
        background_music_path=music_path,
        bgm_volume=args.bgm_volume,
        narration_gain=args.tts_gain,
        enable_tts=True,
        tts_language="zh-cn",
        tts_speaker_wav=xtts_speaker_wav,
        tts_model_path=str(xtts_paths.model_path),
        tts_device=args.tts_device,
        pre_segmented_text=segments,
        pre_highlight_words=highlights,
    )
    print(f"Video saved to: {output_path}")

if __name__ == "__main__":
    main()
