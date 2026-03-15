from collections.abc import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import ColorClip, CompositeVideoClip, ImageClip, vfx

from .config import VideoConfig
from .style_engine import TextStyle


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def _ease_out_back(progress: float) -> float:
    p = _clamp(progress, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def _load_font(font_path: str, font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(font_path, font_size)
    except OSError:
        return ImageFont.load_default()


def _find_highlight_indices(text: str, words: tuple[str, ...]) -> set[int]:
    indices: set[int] = set()
    for word in words:
        if not word:
            continue
        start = text.find(word)
        while start != -1:
            for idx in range(start, start + len(word)):
                indices.add(idx)
            start = text.find(word, start + 1)
    return indices


class ClipBuilder:
    """Generate one animated text clip on top of a black background."""

    def __init__(self, config: VideoConfig) -> None:
        self.config = config

    def build_clip(
        self,
        text: str,
        style: TextStyle,
        duration: float | None = None,
    ) -> CompositeVideoClip:
        if duration is None:
            duration = _clamp(
                len(text) * self.config.seconds_per_char,
                self.config.min_clip_duration,
                self.config.max_clip_duration,
            )
        else:
            duration = max(0.2, float(duration))

        max_text_width = int(self.config.width * self.config.max_text_width_ratio)
        text_image = self._render_styled_text_image(text, style, max_text_width)
        text_clip = ImageClip(text_image).with_duration(duration)

        entry_duration = _clamp(duration * self.config.entry_duration_ratio, 0.35, 0.9)
        position_func = self._build_position_func(style.direction, text_clip.size, entry_duration)
        scale_func = self._build_scale_func(style.direction, entry_duration, style.emphasize)

        animated_text = (
            text_clip.with_position(position_func)
            .with_effects(
                [
                    vfx.Resize(scale_func),
                    vfx.FadeIn(0.18),
                    vfx.FadeOut(0.22),
                    vfx.Rotate(style.rotation, expand=True),
                ]
            )
            .with_duration(duration)
        )

        background = ColorClip(
            size=(self.config.width, self.config.height), color=self.config.bg_color
        ).with_duration(duration)

        return CompositeVideoClip(
            [background, animated_text], size=(self.config.width, self.config.height)
        ).with_duration(duration)

    @staticmethod
    def _render_styled_text_image(text: str, style: TextStyle, max_text_width: int) -> np.ndarray:
        normal_font = _load_font(style.font_path, style.font_size)
        highlight_font_size = max(style.font_size + 8, int(style.font_size * 1.24))
        highlight_font = _load_font(style.font_path, highlight_font_size)

        highlight_indices = _find_highlight_indices(text, style.highlight_words)
        line_gap = max(10, style.font_size // 8)
        char_gap = max(1, style.font_size // 30)

        lines: list[list[tuple[str, int, int, int, int, bool]]] = []
        line: list[tuple[str, int, int, int, int, bool]] = []
        x = 0
        max_line_width = 0

        for idx, char in enumerate(text):
            is_highlight = idx in highlight_indices
            font = highlight_font if is_highlight else normal_font
            left, top, right, bottom = font.getbbox(char)
            glyph_w = max(1, right - left)

            if x > 0 and x + glyph_w > max_text_width:
                lines.append(line)
                max_line_width = max(max_line_width, x - char_gap)
                line = []
                x = 0
            line.append((char, x, left, top, bottom, is_highlight))
            x += glyph_w + char_gap

        if line:
            lines.append(line)
            max_line_width = max(max_line_width, x - char_gap)

        pad_x = 42
        pad_y = 34

        line_metrics: list[tuple[int, int]] = []
        text_height = 0
        for line in lines:
            top_min = min(item[3] for item in line)
            bottom_max = max(item[4] for item in line)
            line_height = max(1, bottom_max - top_min)
            line_metrics.append((top_min, line_height))
            text_height += line_height

        if lines:
            text_height += line_gap * (len(lines) - 1)

        image_width = max(2, max_line_width + pad_x * 2)
        image_height = max(2, text_height + pad_y * 2)

        image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        y_cursor = 0
        for line, (line_top, line_height) in zip(lines, line_metrics, strict=True):
            for char, glyph_x, left, _top, _bottom, is_highlight in line:
                font = highlight_font if is_highlight else normal_font
                fill = style.highlight_color if is_highlight else style.color

                draw_x = glyph_x + pad_x - left
                draw_y = y_cursor + pad_y - line_top

                if is_highlight:
                    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                        draw.text(
                            (draw_x + dx, draw_y + dy),
                            char,
                            font=font,
                            fill=fill,
                            stroke_width=2,
                            stroke_fill="black",
                        )
                else:
                    draw.text(
                        (draw_x, draw_y),
                        char,
                        font=font,
                        fill=fill,
                        stroke_width=2,
                        stroke_fill="black",
                    )
            y_cursor += line_height + line_gap

        return np.asarray(image)

    def _build_position_func(
        self,
        direction: str,
        text_size: tuple[int, int],
        entry_duration: float,
    ) -> Callable[[float], tuple[float, float] | tuple[str, str]]:
        text_width, text_height = text_size
        center_x = (self.config.width - text_width) / 2.0
        center_y = (self.config.height - text_height) / 2.0

        if direction == "center_zoom":
            return lambda _t: ("center", "center")

        # Start from edge-inside positions to avoid MoviePy mask edge bugs.
        if direction == "left":
            start_pos = (24.0, center_y)
        elif direction == "right":
            start_pos = (self.config.width - text_width - 24.0, center_y)
        elif direction == "top":
            start_pos = (center_x, 80.0)
        else:
            start_pos = (center_x, self.config.height - text_height - 80.0)

        end_pos = (center_x, center_y)

        def position_at_time(t: float) -> tuple[float, float]:
            progress = _clamp(t / entry_duration, 0.0, 1.0)
            eased = _ease_out_back(progress)
            x = start_pos[0] + (end_pos[0] - start_pos[0]) * eased
            y = start_pos[1] + (end_pos[1] - start_pos[1]) * eased
            return x, y

        return position_at_time

    @staticmethod
    def _build_scale_func(
        direction: str, entry_duration: float, emphasize: bool
    ) -> Callable[[float], float]:
        start_scale = 0.18 if direction == "center_zoom" else 0.86
        overshoot_scale = 1.14 if emphasize else 1.08
        settle_time = entry_duration + 0.18

        def scale_at_time(t: float) -> float:
            if t <= entry_duration:
                eased = _ease_out_back(t / entry_duration)
                return start_scale + (1.0 - start_scale) * eased

            if t <= settle_time:
                progress = _clamp((t - entry_duration) / 0.18, 0.0, 1.0)
                return 1.0 + (overshoot_scale - 1.0) * (1.0 - progress)

            return 1.0

        return scale_at_time
