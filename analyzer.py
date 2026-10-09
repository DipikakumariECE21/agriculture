"""Leaf image analysis engine.

Pipeline: quality check -> HSV conversion -> leaf segmentation -> lesion isolation
-> connected-component spot statistics -> feature scoring -> softmax probabilities.

Runs on NumPy + Pillow only so it works on a laptop or a Raspberry Pi without a GPU.
The feature vector it produces is the same one a CNN head can later be benchmarked against.
"""

from __future__ import annotations

import base64
import io
import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, UnidentifiedImageError

MAX_SIDE = 512
LABEL_GRID = 160
MIN_LEAF_COVERAGE = 0.08
BLUR_THRESHOLD = 35.0

CLASSES = {
    "healthy": "Healthy Leaf",
    "early-blight": "Early Blight",
    "late-blight": "Late Blight",
    "leaf-spot": "Leaf Spot",
    "rust": "Rust",
    "powdery-mildew": "Powdery Mildew",
    "nutrient-chlorosis": "Nutrient Chlorosis",
}


class AnalysisError(ValueError):
    """Raised when the uploaded file cannot be analysed."""


@dataclass
class AnalysisResult:
    status: str  # "ok" | "unsupported"
    label: str
    slug: str
    confidence: float
    severity: float
    severity_band: str
    probabilities: list[dict]
    features: dict
    adjusted: bool = False
    warnings: list[str] = field(default_factory=list)
    overlay: str = ""
    original: str = ""
    thumbnail: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _encode(img: Image.Image, quality: int = 82) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _load(data: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise AnalysisError("The file is not a readable image. Use JPG, PNG or WebP.") from exc
    if min(img.size) < 64:
        raise AnalysisError("Image is too small. Use a photo at least 64 px on each side.")
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    return img


def _laplacian_variance(gray: np.ndarray) -> float:
    g = gray.astype(np.float32)
    lap = (
        -4 * g[1:-1, 1:-1]
        + g[:-2, 1:-1]
        + g[2:, 1:-1]
        + g[1:-1, :-2]
        + g[1:-1, 2:]
    )
    return float(lap.var())


def _blur_mask(mask: np.ndarray, radius: float) -> np.ndarray:
    m = Image.fromarray((mask * 255).astype(np.uint8), "L")
    return np.asarray(m.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0


def _to_img(mask: np.ndarray) -> Image.Image:
    return Image.fromarray((mask * 255).astype(np.uint8), "L")


def _open(mask: np.ndarray, size: int) -> np.ndarray:
    """Morphological opening: removes thin structures such as leaf veins."""
    img = _to_img(mask).filter(ImageFilter.MinFilter(size)).filter(ImageFilter.MaxFilter(size))
    return np.asarray(img) > 127


def _close(mask: np.ndarray, size: int) -> np.ndarray:
    """Morphological closing: bridges small gaps between leaf-tissue pixels."""
    img = _to_img(mask).filter(ImageFilter.MaxFilter(size)).filter(ImageFilter.MinFilter(size))
    return np.asarray(img) > 127


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill enclosed background (lesion centres) by flood-filling from the border."""
    padded = Image.new("L", (mask.shape[1] + 2, mask.shape[0] + 2), 0)
    padded.paste(_to_img(mask), (1, 1))
    ImageDraw.floodfill(padded, (0, 0), 128)
    arr = np.asarray(padded)[1:-1, 1:-1]
    return arr != 128


def _small_components(mask: np.ndarray, max_px: int) -> np.ndarray:
    """Keep only 4-connected components no larger than max_px (drops enclosed background)."""
    h, w = mask.shape
    keep = np.zeros_like(mask)
    seen = np.zeros_like(mask)
    for y0, x0 in zip(*np.nonzero(mask)):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        q = deque([(y0, x0)])
        pix = []
        while q:
            y, x = q.popleft()
            pix.append((y, x))
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if len(pix) <= max_px:
            ys, xs = zip(*pix)
            keep[list(ys), list(xs)] = True
    return keep


def _components(mask: np.ndarray) -> list[int]:
    """Return pixel areas of 4-connected components on a downsampled mask."""
    h, w = mask.shape
    scale = LABEL_GRID / max(h, w)
    if scale < 1:
        small = Image.fromarray((mask * 255).astype(np.uint8), "L").resize(
            (max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR
        )
        grid = np.asarray(small) > 90
    else:
        grid = mask.copy()
    gh, gw = grid.shape
    seen = np.zeros_like(grid, dtype=bool)
    areas: list[int] = []
    ys, xs = np.nonzero(grid)
    for y0, x0 in zip(ys, xs):
        if seen[y0, x0]:
            continue
        seen[y0, x0] = True
        q = deque([(y0, x0)])
        area = 0
        while q:
            y, x = q.popleft()
            area += 1
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if 0 <= ny < gh and 0 <= nx < gw and grid[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    q.append((ny, nx))
        if area >= 2:
            areas.append(area)
    return areas


def _softmax(scores: dict[str, float], temperature: float = 0.6) -> dict[str, float]:
    mx = max(scores.values())
    exps = {k: math.exp((v - mx) / temperature) for k, v in scores.items()}
    total = sum(exps.values())
    return {k: v / total for k, v in exps.items()}


def _severity_band(pct: float) -> str:
    if pct < 1.5:
        return "None"
    if pct < 6:
        return "Low"
    if pct < 18:
        return "Moderate"
    return "High"


def analyze(data: bytes) -> AnalysisResult:
    img = _load(data)
    rgb = np.asarray(img)
    hsv = np.asarray(img.convert("HSV")).astype(np.float32)
    h = hsv[..., 0] * (360.0 / 255.0)
    s = hsv[..., 1]
    v = hsv[..., 2]
    gray = np.asarray(img.convert("L"))
    total = float(h.size)

    sharpness = _laplacian_variance(gray)
    brightness = float(v.mean())

    green = (h >= 58) & (h <= 170) & (s >= 40) & (v >= 35)
    rusty = (h >= 10) & (h < 32) & (s >= 185) & (v >= 150)
    brown = (((h < 42) & (v <= 205)) | ((h < 50) & (v <= 150))) & (s >= 60) & (v >= 25) & ~rusty
    yellow = _open((h >= 48) & (h < 58) & (s >= 110) & (v >= 140), 5)
    brown &= ~yellow
    pale = (s < 45) & (v >= 70)

    # Segment on a lightly blurred copy so sensor noise / random texture can't pose as leaf,
    # and count chlorotic (yellowed) tissue as leaf so whole-leaf yellowing is still analysed.
    seg = np.asarray(img.filter(ImageFilter.GaussianBlur(1.6)).convert("HSV")).astype(np.float32)
    sh, ss, sv = seg[..., 0] * (360.0 / 255.0), seg[..., 1], seg[..., 2]
    tissue = ((sh >= 58) & (sh <= 170) & (ss >= 45) & (sv >= 35)) | (
        (sh >= 40) & (sh < 58) & (ss >= 100) & (sv >= 110)
    )
    closed = _close(tissue, 9)
    region = _fill_holes(closed)
    holes = _small_components(region & ~closed & (v >= 40) & (v <= 190) & (s >= 30), int(total * 0.012))
    leaf_px = float(region.sum())
    coverage = leaf_px / total

    lesion_types = {
        "brown": brown & region,
        "rust": rusty & region,
        "yellow": yellow & region,
        "white": _open(pale & (v >= 175), 3) & region,
        "dark": holes & ~brown & ~rusty & ~green & ~yellow & ~pale,
    }
    lesion = np.zeros_like(green)
    for m in lesion_types.values():
        lesion |= m
    lesion &= ~green

    denom = max(leaf_px, 1.0)
    ratios = {k: float(m.sum()) / denom for k, m in lesion_types.items()}
    lesion_ratio = float(lesion.sum()) / denom
    very_dark = float((lesion & (v < 90) & ~lesion_types["yellow"]).sum()) / denom

    spot_mask = (lesion_types["brown"] | lesion_types["rust"] | lesion_types["dark"]) & ~green
    areas = _components(spot_mask)
    grid_leaf = max(leaf_px * (LABEL_GRID / max(img.size)) ** 2, 1.0)
    spot_count = len(areas)
    largest = (max(areas) / grid_leaf) if areas else 0.0
    mean_area = (sum(areas) / len(areas) / grid_leaf) if areas else 0.0

    warnings: list[str] = []
    if sharpness < BLUR_THRESHOLD:
        warnings.append("The photo looks blurred. Hold the phone steady and tap to focus on the leaf.")
    if brightness < 55:
        warnings.append("The photo is very dark. Shoot in daylight or move out of shade.")
    elif brightness > 225:
        warnings.append("The photo is over-exposed. Avoid direct glare on the leaf surface.")

    features = {
        "leaf_coverage": round(coverage * 100, 1),
        "lesion_area": round(lesion_ratio * 100, 2),
        "spot_count": spot_count,
        "largest_spot": round(largest * 100, 2),
        "brown_ratio": round(ratios["brown"] * 100, 2),
        "rust_ratio": round(ratios["rust"] * 100, 2),
        "yellow_ratio": round(ratios["yellow"] * 100, 2),
        "white_ratio": round(ratios["white"] * 100, 2),
        "dark_ratio": round(very_dark * 100, 2),
        "mean_spot": round(mean_area * 100, 3),
        "sharpness": round(sharpness, 1),
        "brightness": round(brightness, 1),
        "resolution": f"{img.size[0]}×{img.size[1]}",
    }

    overlay_img = _overlay(img, region, lesion_types, green)
    thumb = img.copy()
    thumb.thumbnail((120, 120))

    if coverage < MIN_LEAF_COVERAGE:
        return AnalysisResult(
            status="unsupported",
            label="No leaf detected",
            slug="",
            confidence=0.0,
            severity=0.0,
            severity_band="—",
            probabilities=[],
            features=features,
            warnings=warnings
            + ["Less than 8% of the frame looks like leaf tissue. Fill the frame with a single leaf and try again."],
            overlay=_encode(overlay_img),
            original=_encode(img),
            thumbnail=_encode(thumb, 70),
        )

    # Stage 1 decides healthy vs diseased from lesion area; stage 2 separates disease types by
    # spot *shape* (count, mean size, share of very dark tissue) rather than raw area.
    count_term = min(spot_count, 40)
    spots = ratios["brown"] + ratios["dark"]
    rust = ratios["rust"]
    yellow_excess = max(ratios["yellow"] - 0.15, 0)
    disease = min(60 * spots, 3.5)
    mean_pct = mean_area * 100
    # In an underexposed photo everything reads as "very dark", so that evidence is ignored.
    dark_share = very_dark / max(lesion_ratio, 1e-6) if brightness >= 70 else 0.0
    scores = {
        "healthy": 2.6 - 90 * (spots + rust) - 20 * max(ratios["yellow"] - 0.03, 0) - 30 * ratios["white"],
        "leaf-spot": disease + 0.03 * count_term - 4 * max(mean_pct - 0.22, 0) - 60 * rust
        - 12 * yellow_excess - 1.0,
        "early-blight": disease + 3 * min(max(mean_pct - 0.22, 0), 0.6) + (0.4 if 2 <= spot_count <= 20 else 0)
        - 4 * max(dark_share - 0.4, 0) - 12 * yellow_excess - 1.2,
        "late-blight": disease + 8 * max(dark_share - 0.35, 0) + 2 * max(mean_pct - 0.7, 0)
        - 12 * yellow_excess - 1.6,
        "rust": 140 * rust + 0.03 * count_term - 1.4,
        "powdery-mildew": 45 * ratios["white"] - 1.4,
        "nutrient-chlorosis": 16 * ratios["yellow"] - 12 * (spots + rust) - 0.4,
    }
    probs = _softmax(scores)
    ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)
    top_slug, top_p = ranked[0]

    severity = 0.0 if top_slug == "healthy" else round(min(lesion_ratio * 100, 100), 1)
    raw_p = top_p
    if sharpness < BLUR_THRESHOLD:
        top_p *= 0.75
    if brightness < 55:
        top_p *= 0.6
    if largest > 0.10 or lesion_ratio > 0.30:
        top_p *= 0.6
        warnings.append(
            "Large brown regions look like soil or background, so this looks like a wide shot. "
            "Move closer so a single leaf fills the photo."
        )
    elif coverage < 0.35:
        top_p *= 0.7
        warnings.append(
            f"The leaf fills only {coverage * 100:.0f}% of the frame — this looks like a wide shot. "
            "Move closer so a single leaf fills the photo."
        )
    if top_p < 0.45:
        warnings.append("Confidence is low — symptoms overlap between classes. Confirm with an agriculture officer.")

    return AnalysisResult(
        status="ok",
        label=CLASSES[top_slug],
        slug=top_slug,
        confidence=round(top_p * 100, 1),
        adjusted=top_p < raw_p,
        severity=severity,
        severity_band="None" if top_slug == "healthy" else _severity_band(severity),
        probabilities=[{"slug": k, "label": CLASSES[k], "p": round(p * 100, 1)} for k, p in ranked],
        features=features,
        warnings=warnings,
        overlay=_encode(overlay_img),
        original=_encode(img),
        thumbnail=_encode(thumb, 70),
    )


def _overlay(img: Image.Image, region: np.ndarray, lesions: dict, green: np.ndarray) -> Image.Image:
    base = np.asarray(img.convert("L").convert("RGB")).astype(np.float32) * 0.42
    rgb = np.asarray(img).astype(np.float32)
    out = np.where(region[..., None], rgb * 0.55 + base * 0.35, base * 0.6)

    palette = {
        "brown": (232, 128, 52),
        "rust": (240, 84, 40),
        "dark": (214, 60, 60),
        "yellow": (246, 206, 70),
        "white": (240, 240, 240),
    }
    for key, colour in palette.items():
        m = lesions[key] & ~green
        if m.any():
            out[m] = out[m] * 0.15 + np.array(colour, dtype=np.float32) * 0.85

    edge = region ^ (_blur_mask(region, 1.2) > 0.75)
    out[edge] = out[edge] * 0.3 + np.array((210, 230, 200), dtype=np.float32) * 0.7
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")
