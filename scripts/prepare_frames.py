"""Remove the Gemini sparkle watermark from the extracted frames and export web assets.

The sparkle is a semi-transparent white overlay at a fixed position:
    out = a * 255 + (1 - a) * original
We estimate the per-pixel alpha map `a` across all frames (median), invert the blend
to recover the original pixels, then inpaint the thin residual edge with OpenCV.

Usage:
    python scripts/prepare_frames.py <frames_dir> [--out static]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

BOX = (1110, 550, 1210, 650)  # x0, y0, x1, y1 search window around the sparkle


def star_mask(frames: list[np.ndarray]) -> np.ndarray:
    x0, y0, x1, y1 = BOX
    acc = np.zeros((y1 - y0, x1 - x0), np.float32)
    for f in frames[::4]:
        g = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        acc += g - cv2.GaussianBlur(g, (0, 0), 8)
    acc /= len(frames[::4])
    mask = (acc > acc.max() * 0.22).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    keep = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    mask = (labels == keep).astype(np.uint8) * 255
    return cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=2)


def estimate_alpha(frames: list[np.ndarray], mask: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = BOX
    wide = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
    samples = []
    for f in frames[::3]:
        crop = f[y0:y1, x0:x1]
        bg = cv2.inpaint(crop, wide, 7, cv2.INPAINT_TELEA).astype(np.float32)
        out = crop.astype(np.float32)
        denom = np.clip(255.0 - bg, 30, None)
        samples.append(np.clip((out - bg) / denom, 0, 0.95).mean(axis=2))
    alpha = np.median(np.stack(samples), axis=0)
    alpha[wide == 0] = 0
    return cv2.GaussianBlur(alpha, (0, 0), 0.6)


def clean(frame: np.ndarray, alpha: np.ndarray, mask: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = BOX
    crop = frame[y0:y1, x0:x1].astype(np.float32)
    a = alpha[..., None]
    restored = np.clip((crop - a * 255.0) / (1.0 - a), 0, 255).astype(np.uint8)
    edge = cv2.subtract(cv2.dilate(mask, np.ones((3, 3), np.uint8)), cv2.erode(mask, np.ones((5, 5), np.uint8)))
    restored = cv2.inpaint(restored, edge, 3, cv2.INPAINT_TELEA)
    soft = cv2.GaussianBlur(cv2.dilate(mask, np.ones((3, 3), np.uint8)), (0, 0), 1.5).astype(np.float32)[..., None] / 255.0
    smoothed = cv2.GaussianBlur(restored, (0, 0), 0.8)
    restored = (restored * (1 - soft * 0.5) + smoothed * soft * 0.5).astype(np.uint8)
    out = frame.copy()
    out[y0:y1, x0:x1] = restored
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("frames", type=Path)
    ap.add_argument("--out", type=Path, default=Path("static"))
    ap.add_argument("--quality", type=int, default=55)
    args = ap.parse_args()

    paths = sorted(args.frames.glob("*.jpg"))
    frames = [cv2.imread(str(p)) for p in paths]
    mask = star_mask(frames)
    alpha = estimate_alpha(frames, mask)
    print(f"{len(frames)} frames · mask px {int((mask > 0).sum())} · alpha max {alpha.max():.2f}")

    frames_out = args.out / "frames"
    frames_out.mkdir(parents=True, exist_ok=True)
    cleaned = []
    for i, f in enumerate(frames, start=1):
        c = clean(f, alpha, mask)
        cleaned.append(c)
        cv2.imwrite(str(frames_out / f"{i:04d}.webp"), c, [cv2.IMWRITE_WEBP_QUALITY, args.quality])

    img_out = args.out / "img"
    img_out.mkdir(parents=True, exist_ok=True)
    jpg = [cv2.IMWRITE_JPEG_QUALITY, 86]
    cv2.imwrite(str(img_out / "field-dawn.jpg"), cleaned[0], jpg)
    cv2.imwrite(str(img_out / "leaf-spots.jpg"), cleaned[-1], jpg)
    cv2.imwrite(str(img_out / "leaf-macro.jpg"), cleaned[209], jpg)

    samples = args.out / "samples"
    samples.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(samples / "sample-leaf-spot.jpg"), cleaned[174][0:720, 260:1100], jpg)
    cv2.imwrite(str(samples / "sample-blight.jpg"), cleaned[229][0:720, 360:1160], jpg)
    cv2.imwrite(str(samples / "sample-healthy.jpg"), cleaned[149][40:720, 330:950], jpg)
    print("done")


if __name__ == "__main__":
    main()
