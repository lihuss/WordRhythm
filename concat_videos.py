#!/usr/bin/env python3
"""
Concatenate multiple video clips into a single final video.
"""

from pathlib import Path
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy import concatenate_videoclips

def concatenate_videos(video_paths: list[str], output_path: str) -> None:
    """
    Concatenate multiple video files into a single output video.
    
    Args:
        video_paths: List of paths to video files to concatenate
        output_path: Path to save the final concatenated video
    """
    clips = []
    
    print("Loading video clips...")
    for path in video_paths:
        print(f"  Loading: {path}")
        clip = VideoFileClip(path)
        clips.append(clip)
        print(f"    Duration: {clip.duration:.2f}s")
    
    print(f"\nConcatenating {len(clips)} clips...")
    final_video = concatenate_videoclips(clips, method="compose")
    output_fps = max(1, int(max((clip.fps or 30) for clip in clips)))
    
    print(f"Writing output video: {output_path}")
    final_video.write_videofile(
        output_path,
        fps=output_fps,
        codec="libx264",
        audio_codec="aac",
        logger="bar"
    )
    
    print("Done!")
    
    # Cleanup
    for clip in clips:
        clip.close()
    final_video.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python concat_videos.py <input1.mp4> <input2.mp4> ... <output.mp4>")
        sys.exit(1)
        
    input_videos = sys.argv[1:-1]
    output_video = sys.argv[-1]
    
    # Verify all input videos exist
    for video in input_videos:
        p = Path(video)
        if not p.exists():
            print(f"Error: Video file not found: {p}")
            sys.exit(1)
    
    concatenate_videos(input_videos, output_video)
    
    print(f"\nFinal video saved to: {output_video}")
