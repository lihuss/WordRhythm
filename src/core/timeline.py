from moviepy import VideoClip, concatenate_videoclips


class TimelineComposer:
    """Concatenate independent clips into one continuous timeline."""

    @staticmethod
    def compose(clips: list[VideoClip]) -> VideoClip:
        if not clips:
            raise ValueError("No clips generated. Input text may be empty.")
        return concatenate_videoclips(clips, method="compose", padding=0)
