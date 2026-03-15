import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class XTTSPaths:
    model_path: Path
    speaker_wav: Path
    speaker_wavs: dict[str, Path]

    def resolve_speaker(self, voice: str) -> Path:
        voice_key = voice.strip().lower()
        if voice_key in self.speaker_wavs:
            return self.speaker_wavs[voice_key]

        available = ", ".join(sorted(self.speaker_wavs.keys())) if self.speaker_wavs else "none"
        raise ValueError(f"XTTS voice '{voice}' is not configured. Available voices: {available}")


def _to_absolute(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (project_root / path).resolve()


def load_xtts_paths(project_root: Path, config_path: Path) -> XTTSPaths:
    if not config_path.exists() or not config_path.is_file():
        raise FileNotFoundError(f"XTTS config file not found: {config_path}")

    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"XTTS config is not valid JSON: {config_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("XTTS config root must be a JSON object")

    model_path = payload.get("model_path")
    speaker_wav = payload.get("speaker_wav")
    speaker_wavs_payload = payload.get("speaker_wavs", {})

    if not isinstance(model_path, str) or not model_path.strip():
        raise ValueError("XTTS config must provide non-empty string field: model_path")

    speaker_wavs: dict[str, Path] = {}
    if speaker_wavs_payload:
        if not isinstance(speaker_wavs_payload, dict):
            raise ValueError("XTTS config field 'speaker_wavs' must be a JSON object")
        for voice_name, voice_path in speaker_wavs_payload.items():
            if not isinstance(voice_name, str) or not voice_name.strip():
                raise ValueError("XTTS config field 'speaker_wavs' has an invalid voice key")
            if not isinstance(voice_path, str) or not voice_path.strip():
                raise ValueError(
                    f"XTTS config field 'speaker_wavs.{voice_name}' must be a non-empty string"
                )
            speaker_wavs[voice_name.strip().lower()] = _to_absolute(project_root, voice_path.strip())

    resolved_default_speaker: Path | None = None
    if isinstance(speaker_wav, str) and speaker_wav.strip():
        resolved_default_speaker = _to_absolute(project_root, speaker_wav.strip())

    if resolved_default_speaker is None:
        if "female" in speaker_wavs:
            resolved_default_speaker = speaker_wavs["female"]
        elif "male" in speaker_wavs:
            resolved_default_speaker = speaker_wavs["male"]
        elif speaker_wavs:
            first_key = next(iter(speaker_wavs))
            resolved_default_speaker = speaker_wavs[first_key]

    if resolved_default_speaker is None:
        raise ValueError(
            "XTTS config must provide 'speaker_wav' or at least one entry in 'speaker_wavs'"
        )

    if "female" not in speaker_wavs:
        speaker_wavs["female"] = resolved_default_speaker

    return XTTSPaths(
        model_path=_to_absolute(project_root, model_path.strip()),
        speaker_wav=resolved_default_speaker,
        speaker_wavs=speaker_wavs,
    )
