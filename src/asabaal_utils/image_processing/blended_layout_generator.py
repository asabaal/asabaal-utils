#!/usr/bin/env python3
"""
blended_layout_generator.py — Create gradient-blended backgrounds with fixed logo layouts in multiple resolutions.

Combines gradient blending and auto-layout to generate compositions in common aspect ratios.
"""

import argparse
import os
import json
import tempfile
from typing import List, Tuple, Dict
from PIL import Image

# Import the existing functionality
from .gradient_blend import GradientBlender

# Copy needed functions from auto_layout to avoid import issues
ANCHOR_POINTS = {
    "TL": (0.05, 0.08),  "TC": (0.50, 0.08),  "TR": (0.95, 0.08),
    "LC": (0.08, 0.50),  "C":  (0.50, 0.50),  "RC": (0.92, 0.50),
    "BL": (0.06, 0.92),  "BC": (0.50, 0.92),  "BR": (0.94, 0.92),
    "T13L": (0.333, 0.14), "T13R": (0.666, 0.14),
    "B13L": (0.333, 0.86), "B13R": (0.666, 0.86),
}

def parse_fixed(spec: str) -> Dict[int, str]:
    fixed = {}
    if not spec: return fixed
    for pair in spec.split(";"):
        pair = pair.strip()
        if not pair: continue
        i, anch = pair.split(":")
        fixed[int(i.strip())] = anch.strip().upper()
    return fixed

def rects_overlap(a, b, margin: int=0) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 + margin <= bx1 or bx2 + margin <= ax1 or ay2 + margin <= by1 or by2 + margin <= ay1)

def find_position(bg_w, bg_h, ov_w, ov_h, anchor_name: str, margin_px: int, jitter_px: int) -> Tuple[int,int]:
    ax, ay = ANCHOR_POINTS.get(anchor_name, (0.5, 0.5))
    cx = int(round(ax * bg_w))
    cy = int(round(ay * bg_h))
    x = cx - ov_w // 2
    y = cy - ov_h // 2
    if jitter_px > 0:
        import random
        x += random.randint(-jitter_px, jitter_px)
        y += random.randint(-jitter_px, jitter_px)
    x = max(margin_px, min(x, bg_w - ov_w - margin_px))
    y = max(margin_px, min(y, bg_h - ov_h - margin_px))
    return x, y

def scale_to_width(img: Image.Image, target_w: int) -> Image.Image:
    if img.width == target_w: return img
    ratio = target_w / float(img.width)
    new_h = max(1, int(round(img.height * ratio)))
    return img.resize((target_w, new_h), Image.Resampling.LANCZOS)

def add_shadow(layer: Image.Image, opacity: int = 120, blur: int = 8, offset: Tuple[int,int]=(3,3)) -> Image.Image:
    if layer.mode != "RGBA":
        layer = layer.convert("RGBA")
    alpha = layer.split()[-1]
    shadow = Image.new("RGBA", layer.size, (0,0,0,0))
    shadow.putalpha(int(opacity))
    from PIL import ImageFilter
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur))
    out = Image.new("RGBA", (layer.width + abs(offset[0]), layer.height + abs(offset[1])), (0,0,0,0))
    out.paste(shadow, (max(offset[0],0), max(offset[1],0)), alpha)
    out.paste(layer, (0,0), layer)
    return out

def compose_variant(bg: Image.Image, overlays: List[Image.Image], scales: List[int], anchors_order: List[str],
                    fixed_map: Dict[int,str], perturb_idx: List[int], margin_frac: float, jitter_frac: float,
                    add_shadow_flag: bool, shadow_opacity: int, shadow_blur: int, seed=None) -> Image.Image:
    if seed is not None:
        import random
        random.seed(seed)
    W, H = bg.size
    margin_px = int(round(W * margin_frac))
    jitter_px = int(round(min(W,H) * jitter_frac))

    placed_rects = []
    canvas = bg.copy().convert("RGBA")

    for i, ov in enumerate(overlays):
        pct = scales[i]
        target_w = max(1, int(round(W * (pct / 100.0))))
        ov_resized = scale_to_width(ov, target_w).convert("RGBA")

        layer = ov_resized
        if add_shadow_flag:
            layer = add_shadow(ov_resized, opacity=shadow_opacity, blur=shadow_blur)

        lw, lh = layer.size

        if i in fixed_map:
            candidates = [fixed_map[i]]
        else:
            candidates = anchors_order[:]
            import random
            random.shuffle(candidates)

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
                scale_pct = int(round(scale_pct * 0.92))
                if scale_pct < 8: break
                target_w = max(1, int(round(W * (scale_pct / 100.0))))
                ov_resized = scale_to_width(ov, target_w).convert("RGBA")
                layer = add_shadow(ov_resized, opacity=shadow_opacity, blur=shadow_blur) if add_shadow_flag else ov_resized
                lw, lh = layer.size

        if not placed:
            x, y = max(margin_px, W - lw - margin_px), max(margin_px, H - lh - margin_px)
            canvas.alpha_composite(layer, dest=(x, y))

    return canvas


COMMON_RESOLUTIONS = {
    "1x1": (1024, 1024),
    "16x9": (1920, 1080),  # Standard HD
    "9x16": (1080, 1920),  # Portrait
    "5x7": (1500, 2100),   # Portrait photo
    "7x5": (2100, 1500),   # Landscape photo
    "4x5": (1080, 1350),   # Social media portrait
    "5x4": (1350, 1080),   # Social media landscape
}


def calculate_scale_factor(base_resolution: Tuple[int, int], target_resolution: Tuple[int, int]) -> float:
    """Calculate how much to scale logos based on resolution change."""
    base_area = base_resolution[0] * base_resolution[1]
    target_area = target_resolution[0] * target_resolution[1]
    area_ratio = target_area / base_area
    
    # Scale with square root of area ratio for proportional sizing
    return (area_ratio ** 0.5)


def create_blended_layout(top_img_path: str, bottom_img_path: str, logo_paths: List[str], 
                         fixed_positions: Dict[int, str], base_scales: List[float],
                         overlap: float, resolutions: Dict[str, Tuple[int, int]],
                         output_dir: str, basename: str) -> None:
    """Generate blended layouts in multiple resolutions."""
    
    print(f"Loading base images...")
    top_img = Image.open(top_img_path).convert("RGBA")
    bottom_img = Image.open(bottom_img_path).convert("RGBA")
    logos = [Image.open(path).convert("RGBA") for path in logo_paths]
    
    # Create base blended background at a reference resolution
    base_resolution = (1920, 1080)  # Use 16:9 as reference
    print(f"Creating gradient blend at {base_resolution}...")
    
    # Resize images to base resolution for blending
    top_resized = top_img.resize(base_resolution, Image.Resampling.LANCZOS)
    bottom_resized = bottom_img.resize(base_resolution, Image.Resampling.LANCZOS)
    
    # Create gradient blend using temp files
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_top, \
         tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_bottom, \
         tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_output:
        
        top_resized.save(temp_top.name)
        bottom_resized.save(temp_bottom.name)
        
        blender = GradientBlender(width=base_resolution[0], height=base_resolution[1], overlap=overlap)
        blend_result = blender.blend_images(temp_top.name, temp_bottom.name, temp_output.name)
        blended_bg = Image.open(temp_output.name).convert("RGBA")
        
        # Clean up temp files
        os.unlink(temp_top.name)
        os.unlink(temp_bottom.name)
        os.unlink(temp_output.name)
    
    # Generate for each resolution
    for aspect_ratio, (width, height) in resolutions.items():
        size_name = f"{width}x{height}"
        print(f"\nGenerating {aspect_ratio} {size_name}...")
        
        # Resize blended background to target resolution
        bg_resized = blended_bg.resize((width, height), Image.Resampling.LANCZOS)
        
        # Calculate scale factor for logos
        scale_factor = calculate_scale_factor(base_resolution, (width, height))
        
        # Adjust logo scales based on resolution
        adjusted_scales = [base_scale * scale_factor for base_scale in base_scales]
        
        # Convert percentage scales to pixel values for this resolution
        pixel_scales = []
        for scale_pct in adjusted_scales:
            # Convert from percentage of background width to pixels
            pixel_width = int(width * (scale_pct / 100.0))
            pixel_scales.append(pixel_width)
        
        # Compose the layout
        composed = compose_variant(
            bg_resized, logos, pixel_scales, [], fixed_positions, [],
            margin_frac=0.03, jitter_frac=0.0,
            add_shadow_flag=True, shadow_opacity=120, shadow_blur=8,
            seed=None
        )
        
        # Save output
        output_name = f"{basename}_{aspect_ratio}.png"
        output_path = os.path.join(output_dir, output_name)
        composed.save(output_path, quality=95)
        print(f"  Saved: {output_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate gradient-blended backgrounds with fixed logo layouts in multiple resolutions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  blended-layout-generator top.png bottom.png \\
    --logos logo1.png logo2.png logo3.png \\
    --fixed "0:TC;1:BL;2:BR" \\
    --config scales.json \\
    --overlap 0.25 \\
    --resolutions 16x9 9x16 1x1
        """
    )
    
    parser.add_argument("top_image", help="Top image for gradient blend")
    parser.add_argument("bottom_image", help="Bottom image for gradient blend")
    parser.add_argument("--logos", nargs="+", required=True, help="Logo images in draw order")
    parser.add_argument("--fixed", required=True, help='Fixed positions (e.g., "0:TC;1:BL;2:BR")')
    parser.add_argument("--config", help="JSON config file with relative scales")
    parser.add_argument("--overlap", type=float, default=0.25, help="Gradient overlap (0.0-1.0)")
    parser.add_argument("--resolutions", nargs="+", default=["16x9", "9x16", "1x1"], 
                       choices=list(COMMON_RESOLUTIONS.keys()),
                       help="Aspect ratios to generate")
    parser.add_argument("--outdir", default="output", help="Output directory")
    parser.add_argument("--basename", default="blended_layout", help="Base filename")
    
    args = parser.parse_args()
    
    os.makedirs(args.outdir, exist_ok=True)
    
    # Parse fixed positions
    fixed_positions = parse_fixed(args.fixed)
    
    # Load scales from config or use defaults
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
        
        base_pct = config.get('base_scale_percent', 20)
        relative_scales = config.get('relative_scales', {})
        
        base_scales = []
        for logo_path in args.logos:
            filename = os.path.splitext(os.path.basename(logo_path))[0].lower()
            scale_factor = 1.0
            for pattern, factor in relative_scales.items():
                if pattern.lower() in filename:
                    scale_factor = factor
                    break
            base_scales.append(base_pct * scale_factor)
    else:
        base_scales = [20.0] * len(args.logos)
    
    # Filter resolutions
    selected_resolutions = {ratio: COMMON_RESOLUTIONS[ratio] for ratio in args.resolutions}
    
    # Generate layouts
    create_blended_layout(
        args.top_image, args.bottom_image, args.logos,
        fixed_positions, base_scales, args.overlap,
        selected_resolutions, args.outdir, args.basename
    )
    
    print(f"\n✅ Complete! Generated {len(args.resolutions)} aspect ratios in {args.outdir}")


if __name__ == "__main__":
    main()