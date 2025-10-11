#!/usr/bin/env python3
"""
auto_layout.py — generate non-overlapping logo/title compositions over a background.

Usage (basic):
  python auto_layout.py background.png \
      --layers asabaal.png ai_logo.png septseason.png \
      --variants 6 --outdir output

Lock certain layers to fixed anchors and let others explore:
  python auto_layout.py bg.png --layers title.png ai.png sept.png me.png \
      --fixed "0:TC;3:BR" --perturb "1,2" --variants 8 \
      --scale-pct-list "28,14,16,22" --margin 0.04 --jitter 0.035

Key ideas:
- Place overlays (PNG with transparency recommended) on a background.
- Try a set of anchor positions (rule-of-thirds grid + corners + center).
- Prevent bounding-box overlap with a margin.
- Optionally 'perturb' selected layers with random jitter around their anchors.
- Produce multiple variants.

Arguments:
  background                 Path to the background image (RGBA/RGB).
  --layers L1 L2 ...         One or more overlay images in draw order (first placed first).
  --variants N               Number of variants to generate (default 6).
  --outdir DIR               Output directory (default ./output).
  --basename NAME            Base filename (default variant).
  --scale-pct-list "a,b,..." Percent-of-background-width for each layer (defaults to 20% for all).
  --config FILE              JSON config file with relative scale factors (see below).
  --min-scale-pct P          Minimum scale percent when auto-downscaling to avoid collisions (default 10).
  --anchors "A,B,..."        Anchor candidates to try (default: TC,BL,BR,TR,BC,LC,RC,TL,C).
  --fixed "i:ANCH;..."       Lock specific layer indices to an anchor (e.g., "0:TC;2:BL).
  --perturb "i,j,..."        Layer indices that can have jitter around the chosen anchor.
  --jitter F                 Max jitter fraction of min(width,height) of background (default 0.03).
  --margin F                 Safety margin as fraction of bg width added around each layer bbox (default 0.03).
  --shadow                   Add a subtle drop shadow for overlays.
  --shadow-opacity A         Shadow opacity 0..255 (default 120).
  --shadow-blur PX           Shadow blur radius (default 8).
  --seed S                   Random seed for reproducibility.

Config File Format (JSON):
  {
    "base_scale_percent": 20,
    "relative_scales": {
      "asabaal": 2.0,
      "psalms": 1.5,
      "the_ai_series": 1.0
    }
  }
  The relative_scales use filename matching (1.0 = same size, 2.0 = double, 0.5 = half).

Anchors:
  TL,TC,TR
  LC,C,RC
  BL,BC,BR

Example:
  python auto_layout.py bg.png --layers title.png ai.png season.png \
    --variants 9 --scale-pct-list "30,16,14" --fixed "0:TC" --perturb "1,2"
"""

import argparse, os, random, json
from typing import List, Tuple, Dict
from PIL import Image, ImageFilter

ANCHOR_POINTS = {
    "TL": (0.05, 0.08),  "TC": (0.50, 0.08),  "TR": (0.95, 0.08),
    "LC": (0.08, 0.50),  "C":  (0.50, 0.50),  "RC": (0.92, 0.50),
    "BL": (0.06, 0.92),  "BC": (0.50, 0.92),  "BR": (0.94, 0.92),
    # rule-of-thirds points (slightly inset to respect bleed)
    "T13L": (0.333, 0.14), "T13R": (0.666, 0.14),
    "B13L": (0.333, 0.86), "B13R": (0.666, 0.86),
}
DEFAULT_ANCHORS = ["TC","BL","BR","TR","BC","LC","RC","TL","C","T13L","T13R","B13L","B13R"]


def parse_indices(spec: str) -> List[int]:
    if not spec: return []
    return [int(s.strip()) for s in spec.split(",") if s.strip().isdigit()]


def parse_fixed(spec: str) -> Dict[int, str]:
    # "0:TC;2:BL"
    fixed = {}
    if not spec: return fixed
    for pair in spec.split(";"):
        pair = pair.strip()
        if not pair: continue
        i, anch = pair.split(":")
        fixed[int(i.strip())] = anch.strip().upper()
    return fixed


def scale_to_width(img: Image.Image, target_w: int) -> Image.Image:
    if img.width == target_w: return img
    ratio = target_w / float(img.width)
    new_h = max(1, int(round(img.height * ratio)))
    return img.resize((target_w, new_h), Image.Resampling.LANCZOS)


def add_shadow(layer: Image.Image, opacity: int = 120, blur: int = 8, offset: Tuple[int,int]=(3,3)) -> Image.Image:
    if layer.mode != "RGBA":
        layer = layer.convert("RGBA")
    # Create alpha-based shadow
    alpha = layer.split()[-1]
    shadow = Image.new("RGBA", layer.size, (0,0,0,0))
    shadow.putalpha(int(opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur))
    # Composite shadow and layer with offset
    out = Image.new("RGBA", (layer.width + abs(offset[0]), layer.height + abs(offset[1])), (0,0,0,0))
    out.paste(shadow, (max(offset[0],0), max(offset[1],0)), alpha)
    out.paste(layer, (0,0), layer)
    return out


def rects_overlap(a, b, margin: int=0) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 + margin <= bx1 or bx2 + margin <= ax1 or ay2 + margin <= by1 or by2 + margin <= ay1)


def find_position(bg_w, bg_h, ov_w, ov_h, anchor_name: str, margin_px: int, jitter_px: int) -> Tuple[int,int]:
    ax, ay = ANCHOR_POINTS.get(anchor_name, (0.5, 0.5))
    cx = int(round(ax * bg_w))
    cy = int(round(ay * bg_h))
    # Convert anchor center to top-left
    x = cx - ov_w // 2
    y = cy - ov_h // 2
    # Jitter
    if jitter_px > 0:
        import random
        x += random.randint(-jitter_px, jitter_px)
        y += random.randint(-jitter_px, jitter_px)
    # Keep within bounds with margin
    x = max(margin_px, min(x, bg_w - ov_w - margin_px))
    y = max(margin_px, min(y, bg_h - ov_h - margin_px))
    return x, y


def compose_variant(bg: Image.Image, overlays: List[Image.Image], scales: List[int], anchors_order: List[str],
                    fixed_map: Dict[int,str], perturb_idx: List[int], margin_frac: float, jitter_frac: float,
                    add_shadow_flag: bool, shadow_opacity: int, shadow_blur: int, seed=None) -> Image.Image:
    if seed is not None:
        random.seed(seed)
    W, H = bg.size
    margin_px = int(round(W * margin_frac))
    jitter_px = int(round(min(W,H) * jitter_frac))

    placed_rects = []
    canvas = bg.copy().convert("RGBA")

    for i, ov in enumerate(overlays):
        # scale overlay to target percent of bg width
        pct = scales[i]
        target_w = max(1, int(round(W * (pct / 100.0))))
        ov_resized = scale_to_width(ov, target_w).convert("RGBA")

        # optional shadow
        layer = ov_resized
        if add_shadow_flag:
            layer = add_shadow(ov_resized, opacity=shadow_opacity, blur=shadow_blur)

        lw, lh = layer.size

        # Choose anchors
        if i in fixed_map:
            candidates = [fixed_map[i]]
        else:
            candidates = anchors_order[:]
            random.shuffle(candidates)

        # Try to place without overlap; if failing, progressively shrink
        placed = False
        scale_pct = pct
        while not placed and scale_pct >= 5:
            for anch in candidates:
                jpx = jitter_px if i in perturb_idx else 0
                x, y = find_position(W, H, lw, lh, anch, margin_px, jpx)
                rect = (x, y, x+lw, y+lh)
                if all(not rects_overlap(rect, r, margin_px) for r in placed_rects):
                    canvas.alpha_composite(layer, dest=(x, y))
                    placed_rects.append(rect)
                    placed = True
                    break
            if not placed:
                # downscale ~8% and retry
                scale_pct = int(round(scale_pct * 0.92))
                if scale_pct < 8: break
                target_w = max(1, int(round(W * (scale_pct / 100.0))))
                ov_resized = scale_to_width(ov, target_w).convert("RGBA")
                layer = add_shadow(ov_resized, opacity=shadow_opacity, blur=shadow_blur) if add_shadow_flag else ov_resized
                lw, lh = layer.size

        if not placed:
            # last resort: place bottom-right with clipping guard
            x, y = max(margin_px, W - lw - margin_px), max(margin_px, H - lh - margin_px)
            canvas.alpha_composite(layer, dest=(x, y))

    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("background")
    ap.add_argument("--layers", nargs="+", required=True)
    ap.add_argument("--variants", type=int, default=6)
    ap.add_argument("--outdir", default="output")
    ap.add_argument("--basename", default="variant")
    ap.add_argument("--scale-pct-list", default=None, help="Comma list; e.g., '30,16,14'")
    ap.add_argument("--min-scale-pct", type=int, default=10)
    ap.add_argument("--anchors", default=",".join(DEFAULT_ANCHORS))
    ap.add_argument("--fixed", default="", help='e.g., "0:TC;2:BL"')
    ap.add_argument("--perturb", default="", help="comma list of indices to jitter")
    ap.add_argument("--jitter", type=float, default=0.03)
    ap.add_argument("--margin", type=float, default=0.03)
    ap.add_argument("--shadow", action="store_true")
    ap.add_argument("--shadow-opacity", type=int, default=120)
    ap.add_argument("--shadow-blur", type=int, default=8)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--config", type=str, help="JSON config file with relative scale factors")
    args = ap.parse_args()

    # Load config file if provided
    config = {}
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            print(f"Error: Config file '{args.config}' not found")
            return
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in config file '{args.config}': {e}")
            return

    os.makedirs(args.outdir, exist_ok=True)

    bg = Image.open(args.background).convert("RGBA")
    overlays = [Image.open(p).convert("RGBA") for p in args.layers]

    # scales - handle config file or CLI
    if 'relative_scales' in config:
        # Convert relative scales to percentages
        base_pct = config.get('base_scale_percent', 20)
        relative_scales = config['relative_scales']
        scales = []
        for i, overlay_path in enumerate(args.layers):
            # Get filename without extension for matching
            filename = os.path.splitext(os.path.basename(overlay_path))[0].lower()
            
            # Find matching scale in config
            scale_factor = 1.0  # default
            for pattern, factor in relative_scales.items():
                if pattern.lower() in filename:
                    scale_factor = factor
                    break
            
            scales.append(int(base_pct * scale_factor))
    elif args.scale_pct_list:
        scales = [int(s.strip()) for s in args.scale_pct_list.split(",")]
        if len(scales) < len(overlays):
            scales = scales + [scales[-1]] * (len(overlays) - len(scales))
    else:
        scales = [20] * len(overlays)

    anchors_order = [a.strip().upper() for a in args.anchors.split(",") if a.strip()]
    fixed_map = parse_fixed(args.fixed)
    perturb_idx = parse_indices(args.perturb)

    # If all layers are fixed, generate only one variant with exact positions
    if fixed_map and len(fixed_map) == len(overlays):
        print("All layers fixed - generating single layout")
        composed = compose_variant(
            bg, overlays, scales, anchors_order, fixed_map, perturb_idx,
            margin_frac=args.margin, jitter_frac=0.0,  # No jitter for fixed layouts
            add_shadow_flag=args.shadow, shadow_opacity=args.shadow_opacity, shadow_blur=args.shadow_blur,
            seed=args.seed
        )
        out_path = os.path.join(args.outdir, f"{args.basename}.png")
        composed.save(out_path)
        print("Saved", out_path)
    else:
        # Generate multiple variants for mixed or unfixed layouts
        for n in range(1, args.variants + 1):
            seed = None if args.seed is None else (args.seed + n)
            composed = compose_variant(
                bg, overlays, scales, anchors_order, fixed_map, perturb_idx,
                margin_frac=args.margin, jitter_frac=args.jitter,
                add_shadow_flag=args.shadow, shadow_opacity=args.shadow_opacity, shadow_blur=args.shadow_blur,
                seed=seed
            )
            out_path = os.path.join(args.outdir, f"{args.basename}_{n:02d}.png")
            composed.save(out_path)
            print("Saved", out_path)


if __name__ == "__main__":
    main()
