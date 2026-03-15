import random
from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont


@dataclass(frozen=True)
class TextStyle:
    color: str
    font_path: str
    font_size: int
    highlight_color: str
    highlight_words: tuple[str, ...]
    direction: str
    rotation: float
    emphasize: bool


class StyleEngine:
    """Assign per-segment visual style to avoid repetitive visuals."""

    def __init__(self, fonts_dir: Path, base_font_size: int = 88, seed: int | None = None) -> None:
        self.random = random.Random(seed)
        self.base_font_size = base_font_size
        self.font_pool = self._discover_fonts(fonts_dir)
        self.long_sentence_threshold = 14

        self.color_pool = ["#FFFFFF", "#FFE35A", "#53F3FF", "#FF9A3C"]
        self.emphasis_color_pool = ["#FF5A5A", "#FF7D3C", "#FF2E63"]
        self.direction_pool = ["left", "right", "top", "bottom", "center_zoom"]
        self.emphasis_keywords = {
            "但是",
            "注意",
            "重点",
            "必须",
            "核心",
            "关键",
            "警告",
            "马上",
            "立刻",
        }
        self.content_keywords = [
            "数学",
            "能力",
            "独创性",
            "天赋",
            "关系",
            "定律",
            "教育",
            "地理因素",
            "与世隔绝",
            "深奥",
            "隐晦",
            "简洁",
            "优雅",
            "独特",
            "方式",
            "前沿",
            "公式",
            "定理",
            "世界",
            "核心",
            "重点",
            "关键",
        ]

    def assign_styles(
        self,
        segments: list[str],
        highlight_overrides: list[tuple[str, ...]] | None = None,
    ) -> list[TextStyle]:
        if highlight_overrides is not None and len(highlight_overrides) != len(segments):
            raise ValueError("highlight_overrides length must equal segments length")

        styles: list[TextStyle] = []
        for index, sentence in enumerate(segments):
            emphasize = self._is_emphasis(sentence)
            color_pool = self.emphasis_color_pool if emphasize else self.color_pool

            size_delta = self.random.uniform(-0.2, 0.2)
            font_size = int(self.base_font_size * (1 + size_delta))
            if emphasize:
                font_size = int(font_size * 1.15)

            override_words = highlight_overrides[index] if highlight_overrides is not None else ()
            if override_words:
                highlight_words = tuple(
                    word for word in override_words if word and word in sentence
                )
            else:
                highlight_words = self._pick_highlight_words(sentence)
            highlight_color = self.random.choice(self.emphasis_color_pool)

            styles.append(
                TextStyle(
                    color=self.random.choice(color_pool),
                    font_path=str(self.random.choice(self.font_pool)),
                    font_size=max(48, font_size),
                    highlight_color=highlight_color,
                    highlight_words=highlight_words,
                    direction=self.random.choice(self.direction_pool),
                    rotation=self.random.uniform(-5.0, 5.0),
                    emphasize=emphasize,
                )
            )

        return styles

    def _is_emphasis(self, sentence: str) -> bool:
        return any(keyword in sentence for keyword in self.emphasis_keywords)

    def _pick_highlight_words(self, sentence: str) -> tuple[str, ...]:
        if len(sentence) < self.long_sentence_threshold:
            return ()

        target_count = 2 if len(sentence) >= 18 else 1
        selected: list[str] = []

        # Prefer semantically stronger words when available.
        for keyword in sorted(self.emphasis_keywords, key=len, reverse=True):
            if keyword in sentence and keyword not in selected:
                selected.append(keyword)
            if len(selected) >= target_count:
                return tuple(selected[:target_count])

        for keyword in sorted(self.content_keywords, key=len, reverse=True):
            if keyword in sentence and keyword not in selected:
                selected.append(keyword)
            if len(selected) >= target_count:
                return tuple(selected[:target_count])

        return tuple(selected[:target_count])

    @staticmethod
    def _font_supports_pi(font_path: Path) -> bool:
        try:
            font = ImageFont.truetype(str(font_path), 64)
            mask = font.getmask("π")
            return mask.getbbox() is not None
        except OSError:
            return False

    @staticmethod
    def _discover_fonts(fonts_dir: Path) -> list[Path]:
        if not fonts_dir.exists():
            raise FileNotFoundError(f"Fonts directory does not exist: {fonts_dir}")

        font_paths = sorted(
            [
                *fonts_dir.glob("*.ttf"),
                *fonts_dir.glob("*.otf"),
                *fonts_dir.glob("*.ttc"),
            ]
        )
        if not font_paths:
            raise FileNotFoundError(
                f"No fonts found in {fonts_dir}. Run download_fonts.py first."
            )

        pi_ready_fonts = [path for path in font_paths if StyleEngine._font_supports_pi(path)]
        return pi_ready_fonts or font_paths
