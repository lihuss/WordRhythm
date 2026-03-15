import re
import wave
from pathlib import Path

import numpy as np


_xtts_model = None
_torch_load_patched = False
_xtts_audio_loader_patched = False


class TTSEngine:
    """Generate per-segment narration clips with XTTS only."""

    def __init__(
        self,
        language: str = "zh-cn",
        speaker_wav: str | None = None,
        model_path: str = "models/TTS/XTTS-v2",
        device: str = "auto",
        retries: int = 3,
    ) -> None:
        self.language = language
        self.speaker_wav = speaker_wav
        self.model_path = model_path
        self.device = device
        self.retries = max(1, retries)

    def synthesize_segments(self, segments: list[str], output_dir: Path) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        normalized_segments = [self._normalize_text(text) for text in segments]
        return self._synthesize_all_xtts(normalized_segments, output_dir)

    def _synthesize_all_xtts(self, segments: list[str], output_dir: Path) -> list[Path]:
        xtts_model = self._load_xtts_model(self.model_path, self.device)

        if not self.speaker_wav:
            raise RuntimeError(
                "XTTS requires --tts-speaker-wav (reference voice file)."
            )
        speaker_wav_path = Path(self.speaker_wav)
        if not speaker_wav_path.exists() or not speaker_wav_path.is_file():
            raise RuntimeError(f"XTTS speaker wav not found: {speaker_wav_path}")

        language = self._normalize_xtts_language(self.language)

        generated_paths: list[Path] = []
        for index, text in enumerate(segments):
            output_path = output_dir / f"{index:04d}.wav"
            self._synthesize_xtts_with_retry(
                xtts_model=xtts_model,
                text=text,
                language=language,
                speaker_wav=speaker_wav_path,
                output_path=output_path,
            )
            generated_paths.append(output_path)
        return generated_paths

    def _synthesize_xtts_with_retry(
        self,
        xtts_model,
        text: str,
        language: str,
        speaker_wav: Path,
        output_path: Path,
    ) -> None:
        if output_path.exists():
            output_path.unlink()

        spoken_text = text.strip() or "嗯"
        last_error: Exception | None = None

        for _ in range(self.retries):
            try:
                wav = xtts_model.tts(
                    spoken_text,
                    speaker_wav=str(speaker_wav),
                    language=language,
                )
                self._save_wav(output_path, np.asarray(wav, dtype=np.float32), sample_rate=24000)
                return
            except Exception as exc:  # pragma: no cover - runtime/model dependent
                last_error = exc

        raise RuntimeError(f"XTTS failed for text: {spoken_text}") from last_error

    @staticmethod
    def _save_wav(output_path: Path, wav: np.ndarray, sample_rate: int) -> None:
        clipped = np.clip(wav, -1.0, 1.0)
        int16_data = (clipped * 32767.0).astype(np.int16)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(int16_data.tobytes())

    @staticmethod
    def _normalize_xtts_language(language: str) -> str:
        language_map = {
            "中文": "zh-cn",
            "zh": "zh-cn",
            "zh-cn": "zh-cn",
            "english": "en",
            "en": "en",
            "spanish": "es",
            "es": "es",
            "french": "fr",
            "fr": "fr",
            "japanese": "ja",
            "ja": "ja",
            "korean": "ko",
            "ko": "ko",
        }
        normalized_key = language.strip().lower()
        return language_map.get(normalized_key, normalized_key)

    @staticmethod
    def _patch_torch_load_for_xtts() -> None:
        global _torch_load_patched
        if _torch_load_patched:
            return

        import torch

        original_torch_load = torch.load

        def compatible_torch_load(*args, **kwargs):
            kwargs.setdefault("weights_only", False)
            return original_torch_load(*args, **kwargs)

        torch.load = compatible_torch_load
        _torch_load_patched = True

    @staticmethod
    def _patch_xtts_audio_loader() -> None:
        global _xtts_audio_loader_patched
        if _xtts_audio_loader_patched:
            return

        import librosa
        import torch
        from TTS.tts.models import xtts as xtts_module

        def load_audio_with_librosa(audiopath, sampling_rate):
            audio, _loaded_sr = librosa.load(audiopath, sr=sampling_rate)
            audio = np.asarray(audio, dtype=np.float32)
            if audio.ndim > 1:
                audio = np.mean(audio, axis=0)
            return torch.from_numpy(audio).unsqueeze(0)

        xtts_module.load_audio = load_audio_with_librosa
        _xtts_audio_loader_patched = True

    @classmethod
    def _load_xtts_model(cls, model_path: str, device: str):
        global _xtts_model
        if _xtts_model is not None:
            return _xtts_model

        try:
            import torch
            from TTS.api import TTS
        except ModuleNotFoundError as exc:
            missing_name = getattr(exc, "name", "")
            if missing_name and missing_name != "TTS":
                raise RuntimeError(
                    f"XTTS dependency missing: {missing_name}. Install required runtime packages."
                ) from exc
            raise RuntimeError("Missing dependency TTS. Install with: pip install TTS") from exc

        cls._patch_torch_load_for_xtts()
        cls._patch_xtts_audio_loader()

        resolved_device = device
        if device == "auto":
            resolved_device = "cuda" if torch.cuda.is_available() else "cpu"

        model_path_obj = Path(model_path)
        if not model_path_obj.exists() or not model_path_obj.is_dir():
            raise RuntimeError(f"XTTS model directory not found: {model_path_obj}")

        _xtts_model = TTS(
            model_path=str(model_path_obj),
            config_path=str(model_path_obj / "config.json"),
        ).to(resolved_device)
        return _xtts_model

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = text.replace("AI", "人工智能")
        # Handle Greek symbols and special characters for XTTS
        normalized = normalized.replace("π", "派")
        normalized = re.sub(r"(?<![A-Za-z])pi(?![A-Za-z])", "派", normalized, flags=re.IGNORECASE)
        
        normalized = re.sub(r"(?<!^)([A-Z])", r" \1", normalized)
        normalized = re.sub(r"(?<=[a-zA-Z])(?=\d)|(?<=\d)(?=[a-zA-Z])", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized.strip()
