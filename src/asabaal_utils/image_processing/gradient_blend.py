#!/usr/bin/env python3
"""
gradient_blend.py — vertically blend two images with a smooth gradient overlap.

Normalization strategy (pre-processing):
- Both inputs are resized to the SAME DIMENSIONS (width × height).
- Width is set to specified width or max(input widths).
- Height is set to the larger of the two resized heights.
- Images are centered when cropping/padding to match dimensions.
- Overlap is applied in the center where the images meet.
  - If 0<V<1: overlap is V fraction of the image height
  - If >=1: overlap is V pixels (exact pixel count)

Post-processing target size:
- You can optionally force a specific final HEIGHT using --out-height.
  If the blend is taller than --out-height, it will be cropped (top/center/bottom).
  If the blend is shorter, it will be padded (transparent by default, or a color via --bg).

Usage:
  python gradient_blend.py top.png bottom.png output.png \
      --width 1080 --overlap 0.28 --ease cosine --out-height 1920 --out-align center --pad

Positional args:
  top      Path to the image that will appear at the TOP.
  bottom   Path to the image that will appear at the BOTTOM.
  output   Path to write the blended image (PNG/JPG).

Options:
  --width W               Normalization width in pixels (default: max(input widths)).
  --height H              Normalization height in pixels (default: auto-calculated).
  --aspect-ratio AR       Target aspect ratio (width/height). Use with width OR height to
                          calculate the other dimension. Error if used with both width+height.
  --overlap V             Overlap size between images. If 0<V<1, interpreted as fraction
                          of the pre-out-height blended canvas; if >=1, interpreted as pixels.
                          Default: 0.25 (25% of blended canvas).
  --ease {linear,cosine}  Easing curve for the gradient (default: cosine for smoother blend).
  --gamma-correct         Blend in linear light (gamma ~2.2) for better perceptual results.

  # Optional exact output control AFTER blending
  --out-height H          Force the final exported height in pixels (crop or pad to this).
  --out-align {top,center,bottom}
                          When cropping a taller image, choose which part to keep (default: center).
  --pad                   If the blended canvas is shorter than --out-height, pad instead of scaling.
  --bg HEX                Background color for padding (default: transparent). Examples:
                          --bg "#000000" (black), --bg "#000000FF" (opaque black),
                          --bg "#FFFFFFFF" (opaque white)

  --quality Q             JPEG quality if saving as .jpg/.jpeg (default 92).
  --preview               Save an extra PNG named <output_basename>_preview_mask.png showing
                          the alpha gradient region for debugging.

Examples:
  # Simple: auto width from inputs, 25% height overlap with smooth cosine ease
  python gradient_blend.py top.jpg bottom.jpg out.png

  # Instagram story style: width 1080, final height 1920, 30% overlap
  python gradient_blend.py top.jpg bottom.jpg story.png --width 1080 --overlap 0.30 --out-height 1920 --out-align center --pad

  # Fixed 300px overlap, linear fade, crop top when trimming to height
  python gradient_blend.py top.jpg bottom.jpg out.png --overlap 300 --ease linear --out-height 1400 --out-align top
"""

import argparse
import math
import os
from typing import Tuple, Optional
from pathlib import Path
from PIL import Image, ImageColor
import numpy as np


class GradientBlender:
    """
    A class for vertically blending two images with a smooth gradient overlap.
    """
    
    def __init__(self, 
                 width: Optional[int] = None,
                 height: Optional[int] = None,
                 aspect_ratio: Optional[float] = None,
                 overlap: float = 0.25,
                 ease: str = "cosine",
                 gamma_correct: bool = False,
                 out_height: Optional[int] = None,
                 out_align: str = "center",
                 pad: bool = False,
                 bg: str = "#00000000",
                 quality: int = 92):
        """
        Initialize the gradient blender.
        
         Args:
             width: Normalization width in pixels (default: max(input widths))
             height: Normalization height in pixels (default: auto-calculated)
             aspect_ratio: Target aspect ratio (width/height). If set with width or height,
                          calculates the other dimension. Conflicts if both width+height set.
             overlap: Overlap amount (0-1 for fraction, >=1 for pixels)
             ease: Easing function ('linear' or 'cosine')
             gamma_correct: Whether to blend in linear light
             out_height: Final exported height in pixels
             out_align: Crop alignment when trimming to out_height
             pad: Whether to pad when blend is shorter than out_height
             bg: Background color for padding
             quality: JPEG quality for output
        """
        self.width = width
        self.height = height
        self.aspect_ratio = aspect_ratio
        self.overlap = overlap
        self.ease = ease
        self.gamma_correct = gamma_correct
        self.out_height = out_height
        self.out_align = out_align
        self.pad = pad
        self.bg = bg
        self.quality = quality
    
    def to_rgba(self, img: Image.Image) -> Image.Image:
        """Convert image to RGBA format."""
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        return img

    def resize_to_dimensions(self, img: Image.Image, target_w: int, target_h: int) -> Image.Image:
        """Resize image to target dimensions, choosing between crop or stretch based on minimal distortion."""
        if img.width == target_w and img.height == target_h:
            return img
            
        img_ar = img.width / img.height
        target_ar = target_w / target_h
        
        # Calculate distortion for both approaches
        stretch_distortion = abs(img_ar - target_ar)
        
        # For crop: calculate how much we'd lose
        crop_w = crop_h = crop_distortion = 0
        if img_ar > target_ar:
            # Image is wider - crop width
            crop_w = int(img.height * target_ar)
            crop_distortion = (img.width - crop_w) / img.width
        else:
            # Image is taller - crop height  
            crop_h = int(img.width / target_ar)
            crop_distortion = (img.height - crop_h) / img.height
        
        # Choose approach with less distortion
        if stretch_distortion <= crop_distortion:
            # Stretch to fit
            return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        else:
            # Crop to fit
            if img_ar > target_ar:
                # Crop width (centered)
                x = (img.width - crop_w) // 2
                cropped = img.crop((x, 0, x + crop_w, img.height))
                return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
            else:
                # Crop height (centered)
                y = (img.height - crop_h) // 2
                cropped = img.crop((0, y, img.width, y + crop_h))
                return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)

    def calculate_target_dimensions(self, top: Image.Image, bottom: Image.Image) -> Tuple[int, int]:
        """Calculate target dimensions based on width, height, and aspect_ratio arguments."""
        # Validate argument combinations
        if self.width is not None and self.height is not None and self.aspect_ratio is not None:
            raise ValueError("Cannot specify both width, height, and aspect_ratio together")
        
        if self.aspect_ratio is not None:
            if self.width is not None:
                # Calculate height from aspect ratio
                target_w = self.width
                target_h = int(round(target_w / self.aspect_ratio))
            elif self.height is not None:
                # Calculate width from aspect ratio
                target_h = self.height
                target_w = int(round(target_h * self.aspect_ratio))
            else:
                # Use aspect ratio with max input dimensions
                max_w = max(top.width, bottom.width)
                max_h = max(top.height, bottom.height)
                
                # Try both orientations and pick the one that fits better
                target_w1 = max_w
                target_h1 = int(round(target_w1 / self.aspect_ratio))
                
                target_h2 = max_h
                target_w2 = int(round(target_h2 * self.aspect_ratio))
                
                # Choose the orientation that requires less scaling of inputs
                scale1 = max(target_w1 / top.width, target_w1 / bottom.width, 
                           target_h1 / top.height, target_h1 / bottom.height)
                scale2 = max(target_w2 / top.width, target_w2 / bottom.width,
                           target_h2 / top.height, target_h2 / bottom.height)
                
                if scale1 <= scale2:
                    target_w, target_h = target_w1, target_h1
                else:
                    target_w, target_h = target_w2, target_h2
        else:
            # No aspect ratio constraint
            if self.width is not None and self.height is not None:
                target_w = self.width
                target_h = self.height
            elif self.width is not None:
                target_w = self.width
                # Calculate height to fit both images after width normalization
                scale_top = target_w / top.width
                scale_bottom = target_w / bottom.width
                h_top = top.height * scale_top
                h_bottom = bottom.height * scale_bottom
                target_h = min(h_top, h_bottom)  # Use smaller to avoid padding
            elif self.height is not None:
                target_h = self.height
                # Calculate width to fit both images after height normalization
                scale_top = target_h / top.height
                scale_bottom = target_h / bottom.height
                w_top = top.width * scale_top
                w_bottom = bottom.width * scale_bottom
                target_w = min(w_top, w_bottom)  # Use smaller to avoid padding
            else:
                # Default: max dimensions
                target_w = max(top.width, bottom.width)
                scale_top = target_w / top.width
                scale_bottom = target_w / bottom.width
                h_top = top.height * scale_top
                h_bottom = bottom.height * scale_bottom
                target_h = min(h_top, h_bottom)
        
        return int(target_w), int(target_h)

    def ease_func(self, t: np.ndarray, kind: str) -> np.ndarray:
        """Apply easing function to gradient."""
        if kind == "linear":
            return t
        else:
            # cosine ease for soft fade
            return (1 - np.cos(np.pi * t)) / 2.0

    def gamma_to_linear(self, arr: np.ndarray, gamma: float = 2.2) -> np.ndarray:
        """Convert from gamma to linear color space."""
        return np.power(arr, gamma)

    def gamma_to_srgb(self, arr: np.ndarray, gamma: float = 2.2) -> np.ndarray:
        """Convert from linear to sRGB color space."""
        return np.power(arr, 1.0 / gamma)

    def blend_linear(self, top_rgba: np.ndarray, bottom_rgba: np.ndarray, 
                    alpha: np.ndarray) -> np.ndarray:
        """Blend two images using linear compositing."""
        top_rgb = top_rgba[..., :3].astype(np.float32) / 255.0
        top_a = (top_rgba[..., 3:4].astype(np.float32) / 255.0) * alpha[..., None]

        bot_rgb = bottom_rgba[..., :3].astype(np.float32) / 255.0
        bot_a = (bottom_rgba[..., 3:4].astype(np.float32) / 255.0)

        if self.gamma_correct:
            top_rgb = self.gamma_to_linear(np.clip(top_rgb, 0, 1))
            bot_rgb = self.gamma_to_linear(np.clip(bot_rgb, 0, 1))

        out_a = top_a + bot_a * (1 - top_a)
        eps = 1e-6
        out_rgb = (top_rgb * top_a + bot_rgb * bot_a * (1 - top_a)) / np.clip(out_a, eps, 1.0)

        if self.gamma_correct:
            out_rgb = self.gamma_to_srgb(np.clip(out_rgb, 0, 16))

        out = np.concatenate([np.clip(out_rgb * 255.0, 0, 255).astype(np.uint8),
                              np.clip(out_a * 255.0, 0, 255).astype(np.uint8)], axis=-1)
        return out

    def crop_or_pad(self, img: Image.Image, target_h: int) -> Image.Image:
        """Crop or pad image to target height."""
        w, h = img.size
        if h == target_h:
            return img
        if h > target_h:
            # crop
            if self.out_align == "top":
                box = (0, 0, w, target_h)
            elif self.out_align == "bottom":
                box = (0, h - target_h, w, h)
            else:
                top = (h - target_h) // 2
                box = (0, top, w, top + target_h)
            return img.crop(box)
        else:
            # shorter than target
            if not self.pad:
                return img  # leave as-is unless --pad
            bg = ImageColor.getcolor(self.bg, "RGBA")
            out = Image.new("RGBA", (w, target_h), bg)
            if self.out_align == "top":
                y = 0
            elif self.out_align == "bottom":
                y = target_h - h
            else:
                y = (target_h - h) // 2
            out.paste(img, (0, y))
            return out

    def blend_images(self, top_path: str, bottom_path: str, output_path: str, 
                    preview: bool = False) -> dict:
        """
        Blend two images with gradient overlap.
        
        Args:
            top_path: Path to top image
            bottom_path: Path to bottom image
            output_path: Path for output image
            preview: Whether to save preview mask
            
        Returns:
            Dictionary with blend results and metadata
        """
        # Load images
        top = self.to_rgba(Image.open(top_path))
        bottom = self.to_rgba(Image.open(bottom_path))

        # Calculate target dimensions based on arguments
        target_w, target_h = self.calculate_target_dimensions(top, bottom)
        
        # Resize both images to exact same dimensions
        top_final = self.resize_to_dimensions(top, target_w, target_h)
        bottom_final = self.resize_to_dimensions(bottom, target_w, target_h)

        # Determine overlap (now both images are same size)
        if 0 < self.overlap < 1:
            # Use fraction of image height
            overlap_px = max(2, int(round(target_h * self.overlap)))
        else:
            overlap_px = max(2, int(round(self.overlap)))

        # Calculate final canvas height
        # Images are stacked vertically with overlap: top + bottom - overlap
        blended_h = target_h + target_h - overlap_px

        # Create canvas
        canvas = Image.new("RGBA", (target_w, blended_h), (0, 0, 0, 0))

        # Position images: top at 0, bottom starts after overlap region
        bottom_y = target_h - overlap_px
        canvas.paste(bottom_final, (0, bottom_y))

        # Build alpha mask for top layer
        # Top image is fully opaque until overlap starts, then fades to 0
        overlap_start = target_h - overlap_px
        overlap_end = target_h

        alpha = np.zeros((blended_h,), dtype=np.float32)
        alpha[:overlap_start] = 1.0  # Fully opaque before overlap
        length = overlap_end - overlap_start
        t = np.linspace(0.0, 1.0, num=length, endpoint=True, dtype=np.float32)
        eased = 1.0 - self.ease_func(t, self.ease)  # 1 -> 0 across overlap
        alpha[overlap_start:overlap_end] = eased
        alpha[overlap_end:] = 0.0  # Fully transparent after overlap
        alpha2d = np.repeat(alpha[:, None], target_w, axis=1)

        # Prepare top layer on full canvas
        top_layer = Image.new("RGBA", (target_w, blended_h), (0, 0, 0, 0))
        top_layer.paste(top_final, (0, 0))

        out_arr = self.blend_linear(np.array(top_layer, dtype=np.uint8),
                                   np.array(canvas, dtype=np.uint8),
                                   alpha2d)
        out_img = Image.fromarray(out_arr, mode="RGBA")

        # Post-process exact output height if requested
        if self.out_height is not None:
            out_img = self.crop_or_pad(out_img, self.out_height)

        # Optional preview of the mask
        preview_path = None
        if preview:
            base, ext = os.path.splitext(output_path)
            preview_path = base + "_preview_mask.png"
            mask_img = Image.fromarray((alpha2d * 255).astype(np.uint8), mode="L")
            mask_img.save(preview_path)

        # Save
        ext = os.path.splitext(output_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            out_img = out_img.convert("RGB")
            out_img.save(output_path, quality=self.quality, optimize=True)
        else:
            out_img.save(output_path)

        return {
            'output_path': output_path,
            'output_size': out_img.size,
            'preview_path': preview_path,
            'overlap_pixels': overlap_px,
            'blended_height': blended_h,
            'final_height': out_img.size[1],
            'top_original_size': (Image.open(top_path).size),
            'bottom_original_size': (Image.open(bottom_path).size)
        }


def parse_args():
    """Parse command line arguments."""
    p = argparse.ArgumentParser(description="Vertically blend two images with a smooth gradient overlap.")
    p.add_argument("top", help="path to the TOP image")
    p.add_argument("bottom", help="path to the BOTTOM image")
    p.add_argument("output", help="path to write blended output (png/jpg)")
    p.add_argument("--width", type=int, default=None, help="normalization width (px). default=max(input widths)")
    p.add_argument("--height", type=int, default=None, help="normalization height (px). default=auto-calculated")
    p.add_argument("--aspect-ratio", type=float, default=None, help="target aspect ratio (width/height). use with width OR height, not both")
    p.add_argument("--overlap", type=float, default=0.25, help="overlap amount: 0-1 => fraction of image height; >=1 => pixels")
    p.add_argument("--ease", choices=["linear", "cosine"], default="cosine", help="gradient easing function")
    p.add_argument("--gamma-correct", action="store_true", help="do blending in linear light (gamma 2.2)")

    # Post-blend exact output control
    p.add_argument("--out-height", type=int, default=None, help="final exported height (px). crop/pad to this")
    p.add_argument("--out-align", choices=["top","center","bottom"], default="center", help="crop anchor when trimming to --out-height")
    p.add_argument("--pad", action="store_true", help="pad when blend is shorter than --out-height (default: no-op)")
    p.add_argument("--bg", type=str, default="#00000000", help="padding color in hex (#RRGGBB or #RRGGBBAA). default transparent")

    p.add_argument("--quality", type=int, default=92, help="JPEG quality if saving as .jpg/.jpeg")
    p.add_argument("--preview", action="store_true", help="save a preview of the gradient mask")
    return p.parse_args()


def blend_images(top_path: str, bottom_path: str, output_path: str, **kwargs) -> dict:
    """
    Convenience function to blend two images.
    
    Args:
        top_path: Path to top image
        bottom_path: Path to bottom image
        output_path: Path for output image
        **kwargs: Additional arguments for GradientBlender
        
    Returns:
        Dictionary with blend results
    """
    blender = GradientBlender(**kwargs)
    return blender.blend_images(top_path, bottom_path, output_path)


def main():
    """Command line interface."""
    args = parse_args()
    
    blender = GradientBlender(
        width=args.width,
        height=args.height,
        aspect_ratio=args.aspect_ratio,
        overlap=args.overlap,
        ease=args.ease,
        gamma_correct=args.gamma_correct,
        out_height=args.out_height,
        out_align=args.out_align,
        pad=args.pad,
        bg=args.bg,
        quality=args.quality
    )
    
    result = blender.blend_images(args.top, args.bottom, args.output, preview=args.preview)
    
    print(f"Saved: {result['output_path']} ({result['output_size'][0]}x{result['output_size'][1]})")
    if result['preview_path']:
        print(f"Preview mask: {result['preview_path']}")


if __name__ == "__main__":
    main()