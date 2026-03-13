import re


class TextSegmenter:
    """Split long text into short semantic chunks for on-screen display."""

    def __init__(self, max_chars_per_segment: int = 20) -> None:
        self.max_chars_per_segment = max_chars_per_segment
        self.min_chars_per_segment = max(6, max_chars_per_segment // 2)
        self._split_pattern = re.compile(r"[。！？!?；;，,、：:\n]+")
        self._punct_pattern = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9]+")
        self._hard_break_keywords = [
            "但是",
            "然而",
            "因此",
            "所以",
            "并且",
            "而且",
            "同时",
            "其中",
            "如果",
            "虽然",
            "然后",
            "可以",
            "能够",
            "因为",
            "并没有",
            "并未",
            "远离",
            "以",
            "在",
            "对",
        ]
        self._avoid_start_chars = set("了的着过地得和与及并而")
        self._protected_phrases = [
            "数学",
            "能力",
            "独创性",
            "天赋",
            "关系",
            "定律",
            "数字",
            "数字关系",
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
        ]

    def segment(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        normalized = re.sub(r"\r\n?", "\n", text.strip())
        raw_parts = self._split_pattern.split(normalized)

        clauses = [self._clean_clause(part) for part in raw_parts]
        clauses = [part for part in clauses if part]

        segments: list[str] = []
        pending = ""
        for clause in clauses:
            if len(clause) > self.max_chars_per_segment:
                if pending:
                    segments.append(pending)
                    pending = ""
                segments.extend(self._split_long_clause(clause))
                continue

            if not pending:
                pending = clause
                continue

            if len(pending) + len(clause) <= self.max_chars_per_segment:
                pending = f"{pending}{clause}"
            elif (
                len(pending) < self.min_chars_per_segment
                and len(pending) + len(clause) <= self.max_chars_per_segment + 2
            ):
                pending = f"{pending}{clause}"
            else:
                segments.append(pending)
                pending = clause

        if pending:
            segments.append(pending)

        merged = self._merge_short_tail(segments)
        return [item for item in merged if item]

    def _clean_clause(self, sentence: str) -> str:
        stripped = sentence.strip()
        if not stripped:
            return ""
        # Keep only Chinese/English/numbers so punctuation never appears in video.
        return self._punct_pattern.sub("", stripped)

    def _split_long_clause(self, sentence: str) -> list[str]:
        chunks: list[str] = []
        current = sentence

        while len(current) > self.max_chars_per_segment:
            take = self._pick_split_index(current)
            if len(current) - take < self.min_chars_per_segment:
                take = max(self.min_chars_per_segment, len(current) - self.min_chars_per_segment)
            take = self._adjust_split_for_protected_phrases(current, take)
            chunks.append(current[:take])
            current = current[take:]

        if current:
            chunks.append(current)

        return chunks

    def _pick_split_index(self, sentence: str) -> int:
        upper = min(self.max_chars_per_segment, len(sentence) - 1)
        lower = min(self.min_chars_per_segment, upper)
        target = (lower + upper) // 2

        best_idx = -1
        best_score = float("inf")
        for keyword in self._hard_break_keywords:
            search_start = lower
            while search_start < upper:
                idx = sentence.find(keyword, search_start)
                if idx == -1 or idx > upper:
                    break
                if idx >= lower:
                    score = abs(idx - target)
                    if score < best_score:
                        best_score = score
                        best_idx = idx
                search_start = idx + 1

        if best_idx != -1:
            return best_idx

        for idx in range(upper, lower - 1, -1):
            if idx < len(sentence) and sentence[idx] in self._avoid_start_chars:
                continue
            return idx

        return upper

    def _adjust_split_for_protected_phrases(self, sentence: str, split_idx: int) -> int:
        adjusted = split_idx
        for phrase in self._protected_phrases:
            start = sentence.find(phrase)
            while start != -1:
                end = start + len(phrase)
                if start < adjusted < end:
                    candidates: list[int] = []
                    for candidate in (start, end):
                        if candidate < self.min_chars_per_segment:
                            continue
                        if candidate > self.max_chars_per_segment:
                            continue
                        if len(sentence) - candidate < self.min_chars_per_segment:
                            continue
                        candidates.append(candidate)
                    if candidates:
                        adjusted = min(candidates, key=lambda value: abs(value - split_idx))
                start = sentence.find(phrase, start + 1)
        return adjusted

    def _merge_short_tail(self, segments: list[str]) -> list[str]:
        if not segments:
            return []

        merged = [segments[0]]
        for segment in segments[1:]:
            if (
                len(segment) < self.min_chars_per_segment
                and len(merged[-1]) + len(segment) <= self.max_chars_per_segment + 2
            ):
                merged[-1] = f"{merged[-1]}{segment}"
            elif (
                len(merged[-1]) < self.min_chars_per_segment
                and len(merged[-1]) + len(segment) <= self.max_chars_per_segment + 2
            ):
                merged[-1] = f"{merged[-1]}{segment}"
            else:
                merged.append(segment)
        return merged
