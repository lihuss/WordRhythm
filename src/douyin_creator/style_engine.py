import random
from dataclasses import dataclass
from pathlib import Path


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
        self.stop_chars = set("的一是在了和与而并及为有他她它这那我你我们你们他们她们它们")

    def assign_styles(self, segments: list[str]) -> list[TextStyle]:
        styles: list[TextStyle] = []
        for sentence in segments:
            emphasize = self._is_emphasis(sentence)
            color_pool = self.emphasis_color_pool if emphasize else self.color_pool

            size_delta = self.random.uniform(-0.2, 0.2)
            font_size = int(self.base_font_size * (1 + size_delta))
            if emphasize:
                font_size = int(font_size * 1.15)

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

        selected.extend(self._ranked_phrase_candidates(sentence, target_count - len(selected)))
        selected = selected[:target_count]
        return tuple(selected)

    def _ranked_phrase_candidates(self, sentence: str, needed: int) -> list[str]:
        if needed <= 0:
            return []

        candidates: list[tuple[float, int, int, str]] = []
        total_len = len(sentence)
        center = total_len / 2.0

        for size in (4, 3, 2):
            if total_len < size:
                continue
            for start in range(0, total_len - size + 1):
                phrase = sentence[start:start + size]
                if not self._is_candidate_phrase(phrase):
                    continue
                mid = start + size / 2.0
                score = size * 3 - abs(mid - center) / max(1.0, total_len)
                if any(char in "数学公式定理能力天赋关系教育独创核心重点关键" for char in phrase):
                    score += 1.6
                candidates.append((score, start, start + size, phrase))

        candidates.sort(key=lambda item: item[0], reverse=True)

        picked: list[str] = []
        ranges: list[tuple[int, int]] = []
        for _score, start, end, phrase in candidates:
            if any(not (end <= left or start >= right) for left, right in ranges):
                continue
            if phrase in picked:
                continue
            picked.append(phrase)
            ranges.append((start, end))
            if len(picked) >= needed:
                break

        return picked

    def _is_candidate_phrase(self, phrase: str) -> bool:
        if len(phrase) < 2:
            return False
        if all(char in self.stop_chars for char in phrase):
            return False
        if phrase[0] in self.stop_chars and len(phrase) <= 2:
            return False
        if phrase[-1] in self.stop_chars and len(phrase) <= 2:
            return False
        return True

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
        return font_paths
