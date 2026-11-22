"""Try this 2: how many video frames does the video encoder need? (make try-video-frames)

The video encoder samples 8 frames, encodes each with ResNet18 and averages
them. This encodes the same clip with 2, 4, 8, 16 and 32 frames and reports
the time, how close each vector is to the 8-frame one, and how close it is to
the product photo of the same sneakers. No Docker needed.

Pass another clip to try it: make try-video-frames VIDEO=sample_data/product_videos/<clip>.mp4
(fetch it first with: git lfs pull --include="<that path>")
"""

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.encoders.factory import EncoderFactory  # noqa: E402
from src.encoders.video import VideoEncoder  # noqa: E402
from src.models.pipeline import Modality  # noqa: E402


def main():
    video = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "sample_data/product_videos/white_sneakers.mp4"
    photo = ROOT / "sample_data/product_images/white_sneakers.jpg"
    if video.read_bytes()[:40].startswith(b"version https://git-lfs"):
        sys.exit(f"{video} is a Git LFS pointer. Fetch it: git lfs pull --include=\"{video.relative_to(ROOT)}\"")

    photo_vec = EncoderFactory().create_encoder(Modality.IMAGE).encode(str(photo))
    results = {}
    for n in (2, 4, 8, 16, 32):
        enc = VideoEncoder(sample_frames=n)
        enc.encode(str(video))  # warm-up, so the timing doesn't include first-call setup
        start = time.time()
        results[n] = (enc.encode(str(video)), time.time() - start)

    base = results[8][0]
    print(f"Clip: {video.name}\n")
    print(f"{'frames':>6} {'encode time':>12} {'similarity to 8 frames':>23} {'similarity to the photo':>24}")
    for n, (vec, secs) in results.items():
        print(f"{n:>6} {secs:>11.2f}s {float(vec @ base):>23.4f} {float(vec @ photo_vec):>24.4f}")


if __name__ == "__main__":
    main()
