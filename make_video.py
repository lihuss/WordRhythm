from argparse import ArgumentParser
import os
from pathlib import Path
import random
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from douyin_creator import TextToVideoPipeline, VideoConfig


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


def _read_text_from_args(args) -> str:
    if args.text:
        return args.text.strip()
    if args.text_file:
        return Path(args.text_file).read_text(encoding="utf-8").strip()
    raise ValueError("Provide --text or --text-file")


def _pick_random_music(musics_dir: Path, seed: int | None) -> Path | None:
    if not musics_dir.exists() or not musics_dir.is_dir():
        return None

    music_files = [
        path
        for path in musics_dir.iterdir()
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    ]
    if not music_files:
        return None

    rng = random.Random(seed)
    return rng.choice(music_files)


def _resolve_xtts_speaker_wav(speaker_wav_arg: str | None, tts_model_path: str) -> str | None:
    if speaker_wav_arg:
        return str(Path(speaker_wav_arg))

    candidate_paths = [
        PROJECT_ROOT / "materials" / "voice_reference.wav",
        Path(tts_model_path) / "samples" / "zh-cn-sample.wav",
        PROJECT_ROOT.parent / "Linly-Dubbing" / "models" / "TTS" / "XTTS-v2" / "samples" / "zh-cn-sample.wav",
    ]

    for candidate in candidate_paths:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def _resolve_xtts_model_path(model_path_arg: str) -> str:
    provided_path = Path(model_path_arg)
    if provided_path.exists() and provided_path.is_dir():
        return str(provided_path)

    fallback_path = PROJECT_ROOT.parent / "Linly-Dubbing" / "models" / "TTS" / "XTTS-v2"
    if fallback_path.exists() and fallback_path.is_dir():
        return str(fallback_path)
    return model_path_arg


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Generate animated Chinese text video using MoviePy.")
    default_threads = max(1, os.cpu_count() or 1)
    parser.add_argument("--text", type=str, help="Input text string.")
    parser.add_argument("--text-file", type=str, help="Path to UTF-8 text file.")
    parser.add_argument("--output", type=str, default="outputs/text_video.mp4", help="Output MP4 path.")
    parser.add_argument("--fonts-dir", type=str, default="materials/fonts", help="Folder with .ttf/.otf fonts.")
    parser.add_argument("--musics-dir", type=str, default="musics", help="Folder with background music.")
    parser.add_argument("--width", type=int, default=1080, help="Output width.")
    parser.add_argument("--height", type=int, default=1920, help="Output height.")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second.")
    parser.add_argument(
        "--threads",
        type=int,
        default=default_threads,
        help=f"FFmpeg thread count (default: CPU cores = {default_threads}).",
    )
    parser.add_argument("--disable-tts", action="store_true", help="Disable TTS dubbing.")
    parser.add_argument(
        "--tts-backend",
        type=str,
        choices=["xtts", "gtts", "edge-tts"],
        default="xtts",
        help="TTS backend. Default follows Linly-Dubbing and uses XTTS.",
    )
    parser.add_argument("--tts-voice", type=str, default="zh-CN-XiaoxiaoNeural", help="Edge-TTS voice name.")
    parser.add_argument("--tts-rate", type=str, default="+0%", help="Edge-TTS speech rate, e.g. +15%.")
    parser.add_argument("--tts-volume", type=str, default="+0%", help="Edge-TTS volume, e.g. +0%.")
    parser.add_argument("--tts-lang", type=str, default="zh-cn", help="TTS language code, e.g. zh-cn.")
    parser.add_argument("--tts-slow", action="store_true", help="Enable slow speaking mode for gTTS.")
    parser.add_argument(
        "--tts-speaker-wav",
        type=str,
        default=None,
        help="Reference speaker wav path for XTTS voice cloning.",
    )
    parser.add_argument(
        "--tts-model-path",
        type=str,
        default="models/TTS/XTTS-v2",
        help="XTTS model directory, fallbacks to online xtts_v2 when missing.",
    )
    parser.add_argument(
        "--tts-device",
        type=str,
        choices=["auto", "cuda", "cpu"],
        default="auto",
        help="Device for XTTS inference.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic styles.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    text = _read_text_from_args(args)
    if not text:
        raise ValueError("Input text is empty.")

    config = VideoConfig(width=args.width, height=args.height, fps=args.fps)
    pipeline = TextToVideoPipeline.create(
        fonts_dir=PROJECT_ROOT / args.fonts_dir,
        config=config,
        seed=args.seed,
    )
    music_path = _pick_random_music(PROJECT_ROOT / args.musics_dir, args.seed)
    if music_path is not None:
        print(f"Using background music: {music_path.name}")
    else:
        print(f"No background music found in: {PROJECT_ROOT / args.musics_dir}")

    xtts_speaker_wav = args.tts_speaker_wav
    xtts_model_path = args.tts_model_path
    if not args.disable_tts and args.tts_backend == "xtts":
        xtts_model_path = _resolve_xtts_model_path(args.tts_model_path)
        xtts_speaker_wav = _resolve_xtts_speaker_wav(args.tts_speaker_wav, xtts_model_path)
        if xtts_speaker_wav is not None:
            print(f"Using XTTS speaker reference: {Path(xtts_speaker_wav).name}")
        else:
            print("XTTS speaker reference not found. Set --tts-speaker-wav to enable XTTS dubbing.")

    output_path = pipeline.render(
        text=text,
        output_path=PROJECT_ROOT / args.output,
        threads=args.threads,
        background_music_path=music_path,
        enable_tts=not args.disable_tts,
        tts_backend=args.tts_backend,
        tts_voice=args.tts_voice,
        tts_rate=args.tts_rate,
        tts_volume=args.tts_volume,
        tts_language=args.tts_lang,
        tts_slow=args.tts_slow,
        tts_speaker_wav=xtts_speaker_wav,
        tts_model_path=xtts_model_path,
        tts_device=args.tts_device,
    )
    print(f"Video saved to: {output_path}")


if __name__ == "__main__":
    main()
