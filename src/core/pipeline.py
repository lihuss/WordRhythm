from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from moviepy import AudioFileClip, CompositeAudioClip, afx, concatenate_audioclips

from .audio.tts_engine import TTSEngine
from .utils.segmentation import TextSegmenter
from .clip_generation import ClipBuilder
from .style_engine import StyleEngine
from .timeline import TimelineComposer
from .config import VideoConfig


@dataclass
class TextToVideoPipeline:
    segmenter: TextSegmenter
    style_engine: StyleEngine
    clip_builder: ClipBuilder
    timeline_composer: TimelineComposer
    config: VideoConfig

    @classmethod
    def create(
        cls,
        fonts_dir: Path,
        config: VideoConfig | None = None,
        seed: int | None = None,
    ) -> "TextToVideoPipeline":
        effective_config = config or VideoConfig()
        return cls(
            segmenter=TextSegmenter(effective_config.max_chars_per_segment),
            style_engine=StyleEngine(
                fonts_dir=fonts_dir,
                base_font_size=effective_config.base_font_size,
                seed=seed,
            ),
            clip_builder=ClipBuilder(effective_config),
            timeline_composer=TimelineComposer(),
            config=effective_config,
        )

    def render(
        self,
        text: str,
        output_path: Path,
        threads: int = 4,
        background_music_path: Path | None = None,
        bgm_volume: float = 0.18,
        narration_gain: float = 1.35,
        enable_tts: bool = True,
        tts_language: str = "zh-cn",
        tts_speaker_wav: str | None = None,
        tts_model_path: str = "models/TTS/XTTS-v2",
        tts_device: str = "auto",
        pre_segmented_text: list[str] | None = None,
        pre_highlight_words: list[tuple[str, ...]] | None = None,
    ) -> Path:
        if pre_segmented_text is not None:
            segments = [segment.strip() for segment in pre_segmented_text if segment.strip()]
        else:
            segments = self.segmenter.segment(text)

        if not segments:
            raise ValueError("Input text is empty after segmentation.")

        if pre_highlight_words is not None and len(pre_highlight_words) != len(segments):
            raise ValueError("pre_highlight_words length must match segment count")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        tts_audio_clips: list[AudioFileClip] = []
        tts_temp_dir: Path | None = None
        segment_durations: list[float] | None = None
        narration_audio = None

        styles = self.style_engine.assign_styles(segments, highlight_overrides=pre_highlight_words)
        if enable_tts:
            tts_engine = TTSEngine(
                language=tts_language,
                speaker_wav=tts_speaker_wav,
                model_path=tts_model_path,
                device=tts_device,
            )
            tts_temp_dir = Path(tempfile.mkdtemp(prefix="tts_segments_", dir=str(output_path.parent)))
            segment_audio_paths = tts_engine.synthesize_segments(segments, tts_temp_dir)

            segment_durations = []
            for audio_path in segment_audio_paths:
                audio_clip = AudioFileClip(str(audio_path))
                tts_audio_clips.append(audio_clip)
                segment_durations.append(audio_clip.duration)

            narration_audio = concatenate_audioclips(tts_audio_clips).with_effects(
                [
                    afx.AudioNormalize(),
                    afx.MultiplyVolume(max(0.1, narration_gain)),
                ]
            )

        clips = [
            self.clip_builder.build_clip(segment, style, duration)
            for segment, style, duration in zip(
                segments,
                styles,
                segment_durations or [None] * len(segments),
                strict=True,
            )
        ]

        final_video = None
        background_music = None
        final_audio = None
        try:
            final_video = self.timeline_composer.compose(clips)
            audio_tracks = []

            if narration_audio is not None:
                audio_tracks.append(narration_audio)

            if background_music_path is not None:
                background_music = AudioFileClip(str(background_music_path))
                if background_music.duration < final_video.duration:
                    background_music = background_music.with_effects(
                        [afx.AudioLoop(duration=final_video.duration)]
                    )
                else:
                    background_music = background_music.subclipped(0, final_video.duration)
                background_music = background_music.with_effects(
                    [afx.MultiplyVolume(max(0.0, bgm_volume))]
                )
                audio_tracks.append(background_music)

            if audio_tracks:
                if len(audio_tracks) == 1:
                    final_audio = audio_tracks[0]
                else:
                    final_audio = CompositeAudioClip(audio_tracks).with_duration(final_video.duration)
                final_video = final_video.with_audio(final_audio)

            final_video.write_videofile(
                str(output_path),
                fps=self.config.fps,
                codec="libx264",
                audio_codec="aac",
                threads=threads,
                logger="bar",
            )
            return output_path
        finally:
            if final_audio is not None and final_audio is not narration_audio and final_audio is not background_music:
                final_audio.close()
            if narration_audio is not None:
                narration_audio.close()
            for audio_clip in tts_audio_clips:
                audio_clip.close()
            if background_music is not None:
                background_music.close()
            if final_video is not None:
                final_video.close()
            for clip in clips:
                clip.close()
            if tts_temp_dir is not None and tts_temp_dir.exists():
                shutil.rmtree(tts_temp_dir, ignore_errors=True)
