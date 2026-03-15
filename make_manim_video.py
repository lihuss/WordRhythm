from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys
import tempfile

from moviepy import AudioFileClip, CompositeAudioClip, VideoFileClip, afx, concatenate_audioclips, vfx


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from core.audio.tts_engine import TTSEngine
from core.xtts_paths import load_xtts_paths


AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".opus"}


_CN_NUM = {
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
    "10": "十",
}


def _to_cn_number(token: str) -> str:
    return _CN_NUM.get(token, token)


def _resolve_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def _normalize_formula_for_tts(line: str) -> str:
    text = line.replace("\ufeff", "").strip()
    if not text:
        return ""

    text = text.replace("\\pi", "派").replace("π", "派")

    text = re.sub(
        r"\^\{(\d+)\/(\d+)\}",
        lambda m: f"的{_to_cn_number(m.group(2))}分之{_to_cn_number(m.group(1))}次方",
        text,
    )
    text = re.sub(
        r"\^\{(\d+)\}",
        lambda m: "的平方" if m.group(1) == "2" else f"的{_to_cn_number(m.group(1))}次方",
        text,
    )
    text = re.sub(
        r"\^(\d+)",
        lambda m: "的平方" if m.group(1) == "2" else f"的{_to_cn_number(m.group(1))}次方",
        text,
    )

    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", lambda m: f"{m.group(2)}分之{m.group(1)}", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", lambda m: f"根号{m.group(1)}", text)

    text = text.replace("=", " 等于 ")
    text = text.replace("+", " 加 ")
    text = text.replace("-", " 减 ")
    text = text.replace("/", " 除以 ")
    text = text.replace("(", " ").replace(")", " ")
    text = text.replace("{", " ").replace("}", " ")
    text = text.replace("\\", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _read_narration_lines(script_file: Path) -> list[str]:
    if not script_file.exists() or not script_file.is_file():
        raise FileNotFoundError(f"TTS script file not found: {script_file}")

    lines = [line.strip() for line in script_file.read_text(encoding="utf-8-sig").splitlines()]
    lines = [line for line in lines if line and not line.startswith("#")]
    if not lines:
        raise ValueError(f"TTS script file is empty: {script_file}")

    normalized = [_normalize_formula_for_tts(line) for line in lines]
    return [line for line in normalized if line]


def _find_rendered_mp4(media_dir: Path, file_stem: str) -> Path:
    candidates = list(media_dir.glob(f"videos/**/{file_stem}.mp4"))
    if not candidates:
        raise FileNotFoundError(f"No rendered MP4 found under {media_dir}")
    return max(candidates, key=lambda path: path.stat().st_mtime)


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


def _dub_video_with_tts(video_path: Path, args, bgm_path: Path | None) -> None:
    script_file = PROJECT_ROOT / args.tts_script_file
    lines = _read_narration_lines(script_file)

    xtts_paths = load_xtts_paths(PROJECT_ROOT, _resolve_path(PROJECT_ROOT, args.xtts_config))
    xtts_model_path = str(
        _resolve_path(PROJECT_ROOT, args.tts_model_path) if args.tts_model_path else xtts_paths.model_path
    )
    if args.tts_speaker_wav:
        xtts_speaker_wav = str(_resolve_path(PROJECT_ROOT, args.tts_speaker_wav))
    else:
        xtts_speaker_wav = str(xtts_paths.resolve_speaker(args.voice))
    if not Path(xtts_model_path).exists():
        raise FileNotFoundError(f"XTTS model directory not found: {xtts_model_path}")
    if not Path(xtts_speaker_wav).exists():
        raise FileNotFoundError(f"XTTS speaker wav not found: {xtts_speaker_wav}")

    engine = TTSEngine(
        language=args.tts_lang,
        speaker_wav=xtts_speaker_wav,
        model_path=xtts_model_path,
        device=args.tts_device,
    )

    tts_temp_dir = Path(tempfile.mkdtemp(prefix="tts_manim_", dir=str(video_path.parent)))
    audio_segments: list[AudioFileClip] = []
    narration_audio = None
    bgm_audio = None
    video_clip = None
    final_video = None
    temp_output = video_path.with_name(f"{video_path.stem}.dub_tmp.mp4")

    try:
        segment_paths = engine.synthesize_segments(lines, tts_temp_dir)
        for path in segment_paths:
            audio_segments.append(AudioFileClip(str(path)))

        narration_audio = concatenate_audioclips(audio_segments).with_effects(
            [
                afx.AudioNormalize(),
                afx.MultiplyVolume(max(0.1, args.tts_gain)),
            ]
        )

        video_clip = VideoFileClip(str(video_path))
        if narration_audio.duration > video_clip.duration:
            factor = max(0.2, video_clip.duration / narration_audio.duration)
            video_clip = video_clip.with_effects([vfx.MultiplySpeed(factor=factor)])

        tracks = [narration_audio]
        bgm_clip = None
        if bgm_path is not None:
            if bgm_path.exists() and bgm_path.is_file():
                bgm_clip = AudioFileClip(str(bgm_path))
                if bgm_clip.duration < video_clip.duration:
                    bgm_clip = bgm_clip.with_effects([afx.AudioLoop(duration=video_clip.duration)])
                else:
                    bgm_clip = bgm_clip.subclipped(0, video_clip.duration)
                bgm_clip = bgm_clip.with_effects([afx.MultiplyVolume(max(0.0, args.bgm_volume))])
                tracks.append(bgm_clip)

        mixed_audio = tracks[0] if len(tracks) == 1 else CompositeAudioClip(tracks).with_duration(video_clip.duration)

        final_video = video_clip.with_audio(mixed_audio)
        final_video.write_videofile(
            str(temp_output),
            fps=args.fps,
            codec="libx264",
            audio_codec="aac",
            logger="bar",
        )

        final_video.close()
        video_clip.close()
        narration_audio.close()
        if bgm_clip:
            bgm_clip.close()
        for clip in audio_segments:
            clip.close()

        if video_path.exists():
            try:
                video_path.unlink()
            except PermissionError:
                # Fallback to copy/rename if unlink fails
                print(f"Warning: Could not delete {video_path}, it might be locked. Trying alternative.")
                pass
        
        shutil.move(str(temp_output), str(video_path))
    finally:
        pass

        if temp_output.exists():
            temp_output.unlink()
        if tts_temp_dir.exists():
            shutil.rmtree(tts_temp_dir, ignore_errors=True)


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Generic Manim render + optional TTS dubbing.")
    parser.add_argument("--scene-file", type=str, required=True, help="Path to Manim scene .py file")
    parser.add_argument("--scene-name", type=str, required=True, help="Scene class name")
    parser.add_argument("--output", type=str, required=True, help="Final MP4 output path")
    parser.add_argument("--quality", type=str, choices=["l", "m", "h", "p", "k"], default="h")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--resolution", type=str, default="1080,1920")
    parser.add_argument("--media-dir", type=str, default="outputs/_manim_media")

    parser.add_argument("--disable-tts", action="store_true")
    parser.add_argument("--tts-script-file", type=str, default="")
    parser.add_argument("--tts-lang", type=str, default="zh-cn")
    parser.add_argument(
        "--voice",
        type=str,
        choices=["female", "male"],
        default="female",
        help="Voice preset name from xtts_config speaker_wavs (default: female).",
    )
    parser.add_argument("--tts-speaker-wav", type=str, default="")
    parser.add_argument("--tts-model-path", type=str, default="")
    parser.add_argument(
        "--xtts-config",
        type=str,
        default="xtts_config.json",
        help="Path to XTTS config JSON with model_path and speaker_wav/speaker_wavs.",
    )
    parser.add_argument("--tts-device", type=str, choices=["auto", "cuda", "cpu"], default="auto")
    parser.add_argument("--tts-gain", type=float, default=1.35)

    parser.add_argument("--musics-dir", type=str, default="materials/musics", help="Folder with background music.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for deterministic background music selection.")
    parser.add_argument("--no-bgm", action="store_true", help="Disable background music completely.")
    parser.add_argument("--bgm-path", type=str, default="")
    parser.add_argument("--bgm-volume", type=float, default=0.12)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    scene_file = PROJECT_ROOT / args.scene_file
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    media_dir = PROJECT_ROOT / args.media_dir
    media_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "manim",
        "render",
        str(scene_file),
        args.scene_name,
        "--format",
        "mp4",
        "--quality",
        args.quality,
        "--fps",
        str(args.fps),
        "--resolution",
        args.resolution,
        "--media_dir",
        str(media_dir),
        "--output_file",
        output_path.stem,
    ]

    print("Running:", " ".join(command))
    subprocess.run(command, check=True, cwd=PROJECT_ROOT)

    rendered = _find_rendered_mp4(media_dir, output_path.stem)
    if rendered.resolve() != output_path.resolve():
        shutil.copy2(rendered, output_path)

    resolved_bgm_path: Path | None = None
    if args.no_bgm:
        print("Background music disabled by --no-bgm")
    elif args.bgm_path:
        resolved_bgm_path = _resolve_path(PROJECT_ROOT, args.bgm_path)
        print(f"Using background music: {resolved_bgm_path.name}")
    else:
        resolved_bgm_path = _pick_random_music(PROJECT_ROOT / args.musics_dir, args.seed)
        if resolved_bgm_path is not None:
            print(f"Using background music: {resolved_bgm_path.name}")
        else:
            print(f"No background music found in: {PROJECT_ROOT / args.musics_dir}")

    if not args.disable_tts:
        if not args.tts_script_file:
            raise ValueError("--tts-script-file is required unless --disable-tts is set")
        print("Generating TTS narration and dubbing Manim video...")
        _dub_video_with_tts(output_path, args, resolved_bgm_path)

    print(f"MP4 generated: {output_path}")


if __name__ == "__main__":
    main()
