#!/usr/bin/env python3
"""Extract one frame per second from a video and save as JPG images."""

import argparse
import os
import sys

import cv2


def extract_frames(video_path: str, output_dir: str, fps: float = 1.0) -> int:
    """
    Extract frames from a video at the specified rate.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save extracted frames.
        fps: Number of frames to extract per second of video.

    Returns:
        Number of frames extracted.
    """
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}", file=sys.stderr)
        return 0

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / video_fps if video_fps > 0 else 0

    print(f"Video: {video_path}")
    print(f"  FPS: {video_fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {duration_sec:.2f}s")
    print(f"  Extracting {fps:.2f} frame(s) per second -> {output_dir}")

    frame_interval = int(round(video_fps / fps))
    if frame_interval < 1:
        frame_interval = 1

    extracted = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            timestamp_sec = frame_idx / video_fps
            output_path = os.path.join(
                output_dir, f"frame_{timestamp_sec:06.2f}s.jpg"
            )
            cv2.imwrite(output_path, frame)
            extracted += 1

        frame_idx += 1

    cap.release()
    print(f"Done. Extracted {extracted} frames.")
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract frames from a video at a given rate."
    )
    parser.add_argument("--video", default="./BP-video/BP_correct.mp4",
                        help="Path to input video file.")
    parser.add_argument("--output", default="./BP-video/frames",
                        help="Directory to save extracted frames.")
    parser.add_argument("--fps", type=float, default=1.0,
                        help="Frames to extract per second of video.")
    args = parser.parse_args()

    extract_frames(args.video, args.output, args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
