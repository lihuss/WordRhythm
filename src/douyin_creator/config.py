from dataclasses import dataclass


@dataclass(frozen=True)
class VideoConfig:
    width: int = 1080
    height: int = 1920
    fps: int = 30
    bg_color: tuple[int, int, int] = (0, 0, 0)

    base_font_size: int = 88
    max_chars_per_segment: int = 16

    seconds_per_char: float = 0.3
    min_clip_duration: float = 2.0
    max_clip_duration: float = 4.0

    max_text_width_ratio: float = 0.82
    entry_duration_ratio: float = 0.35
