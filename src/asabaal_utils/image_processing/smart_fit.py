#!/usr/bin/env python3
"""
Minimal-change crop+stretch to a target size.

Usage:
  python smart_fit.py input.jpg output.jpg --width 1920 --height 1080 --max-stretch 0.05 --gravity center

- --max-stretch is the maximum allowed anisotropic stretch (e.g., 0.05 = 5%).
  The script crops to get within that tolerance, then stretches the small remainder.
"""

from PIL import Image, ImageOps
import argparse
from typing import Tuple

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("input", help="Input image path")
    p.add_argument("output", help="Output image path")
    p.add_argument("--width", type=int, required=True, help="Target width, e.g. 1920")
    p.add_argument("--height", type=int, required=True, help="Target height, e.g. 1080")
    p.add_argument("--max-stretch", type=float, default=0.05,
                   help="Max allowed anisotropic stretch ratio (default 0.05 = 5%)")
    p.add_argument("--gravity", choices=["center","top","bottom","left","right"], default="center",
                   help="Crop anchor (default: center)")
    return p.parse_args()

def compute_crop_box(W:int, H:int, target_aspect:float, stretch_tol:float, gravity:str) -> Tuple[int,int,int,int]:
    """
    Return (left, top, right, bottom) crop box that makes the cropped area aspect
    within [target_aspect/(1+tol), target_aspect*(1+tol)]. If original aspect is already
    within tolerance, returns full image.
    """
    s_aspect = W / H
    low = target_aspect / (1.0 + stretch_tol)
    high = target_aspect * (1.0 + stretch_tol)

    # Already within tolerance: no crop
    if low <= s_aspect <= high:
        return (0, 0, W, H)

    if s_aspect > high:
        # Too wide: crop width
        # choose width to reach "high" boundary (least crop while staying within tol)
        crop_w = int(round(H * high))
        crop_w = min(crop_w, W)
        if gravity == "left":
            left = 0
        elif gravity == "right":
            left = W - crop_w
        else:  # center/top/bottom treated as horizontal center
            left = (W - crop_w) // 2
        return (left, 0, left + crop_w, H)
    else:
        # Too tall/narrow: crop height
        crop_h = int(round(W / low))
        crop_h = min(crop_h, H)
        if gravity == "top":
            top = 0
        elif gravity == "bottom":
            top = H - crop_h
        else:  # center/left/right treated as vertical center
            top = (H - crop_h) // 2
        return (0, top, W, top + crop_h)

def minimal_change_fit(img: Image.Image,
                       target_size: Tuple[int,int],
                       max_stretch: float = 0.05,
                       gravity: str = "center") -> Image.Image:
    """
    1) Smart-crop to get the aspect ratio within a stretch tolerance.
    2) Non-uniform resize the remainder (small stretch) to hit exact pixels.

    Returns a new PIL Image at target_size.
    """
    # Respect EXIF orientation (iOS photos, etc.)
    img = ImageOps.exif_transpose(img)

    Tw, Th = target_size
    W, H = img.size
    target_aspect = Tw / Th

    # Step 1: crop just enough to bring aspect within tolerance
    box = compute_crop_box(W, H, target_aspect, max_stretch, gravity)
    if box != (0, 0, W, H):
        img = img.crop(box)

    # Step 2: final stretch (often very small) to land exactly on target size
    # Note: this may be anisotropic but constrained by our tolerance in step 1
    result = img.resize((Tw, Th), resample=Image.LANCZOS)
    return result

def process_image(in_path: str,
                  out_path: str,
                  target_size: Tuple[int,int],
                  max_stretch: float = 0.05,
                  gravity: str = "center") -> None:
    with Image.open(in_path) as im:
        out = minimal_change_fit(im, target_size, max_stretch=max_stretch, gravity=gravity)
        # Keep original format if possible, default to PNG if unknown
        save_kwargs = {}
        fmt = (im.format or "PNG").upper()
        if fmt in ("JPEG", "JPG"):
            # sensible default quality; tweak if you like
            save_kwargs.update({"quality": 92, "subsampling": "4:2:0"})
            fmt = "JPEG"
        out.save(out_path, format=fmt, **save_kwargs)

if __name__ == "__main__":
    args = parse_args()
    process_image(args.input,
                  args.output,
                  (args.width, args.height),
                  max_stretch=args["max_stretch"] if isinstance(args, dict) else args.max_stretch,
                  gravity=args.gravity)

