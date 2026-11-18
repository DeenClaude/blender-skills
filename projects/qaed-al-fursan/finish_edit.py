"""
Finishing pass: soft dissolves between the 12 shots, then H.264 encode.

    python3 finish_edit.py render/frames_final render/qaed_al_fursan_final.mp4

Each cut becomes an 8-frame (1/3 s) dissolve centred on the cut, blended in
linear light so brightness doesn't dip. The outgoing shot holds its last frame
and the incoming shot holds its first, so no extra frames need rendering and
the film stays exactly 384 frames (16 s). Needs: numpy, pillow, ffmpeg.
"""
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

CUTS = [49, 97, 121, 145, 193, 241, 265, 289, 313, 337, 361]   # first frame of shots 02-12
HALF = 4                                                      # dissolve = 2 * HALF frames
FRAMES = 384


def load(d, f):
    return np.asarray(Image.open(os.path.join(d, f"f_{f:04d}.png")).convert("RGB"), dtype=np.float32) / 255.0


def main(src, out_mp4, crf="16"):
    tmp = tempfile.mkdtemp(prefix="qaf_edit_")
    try:
        blend = {}
        for c in CUTS:
            a = load(src, c - 1) ** 2.2
            b = load(src, c) ** 2.2
            for k in range(-HALF, HALF):
                f = c + k
                t = (k + HALF + 0.5) / (2 * HALF)
                t = t * t * (3 - 2 * t)                       # ease in/out
                fa = load(src, f) ** 2.2 if f < c else a
                fb = load(src, f) ** 2.2 if f >= c else b
                blend[f] = (fa * (1 - t) + fb * t) ** (1 / 2.2)
        for f in range(1, FRAMES + 1):
            dst = os.path.join(tmp, f"f_{f:04d}.png")
            if f in blend:
                Image.fromarray(np.clip(blend[f] * 255 + 0.5, 0, 255).astype(np.uint8)).save(dst)
            else:
                shutil.copyfile(os.path.join(src, f"f_{f:04d}.png"), dst)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24",
                        "-i", os.path.join(tmp, "f_%04d.png"), "-c:v", "libx264", "-preset", "slow",
                        "-crf", crf, "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4], check=True)
        print("wrote", out_mp4)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *(sys.argv[3:4]))
