#!/usr/bin/env python3
"""
AI Media Cost Break-even Calculator

Compare a flat monthly subscription (e.g., Midjourney) against pay-per-use API pricing
for image + video generation. Computes total monthly cost for your usage and estimates
the video-seconds break-even given your image usage and API unit prices.

Usage examples:
  # 1) Single scenario
  python ai_media_breakeven.py \
    --subscription 48 \
    --video-sec 215 \
    --api-video-per-sec 0.20 \
    --images 100 \
    --api-image-each 0.05

  # 2) Find the video-seconds break-even for your image usage
  python ai_media_breakeven.py \
    --subscription 48 \
    --api-video-per-sec 0.20 \
    --images 100 \
    --api-image-each 0.05 \
    --show-breakeven

  # 3) Sweep a range of video usage (seconds) and print a table
  python ai_media_breakeven.py \
    --subscription 48 \
    --api-video-per-sec 0.10 \
    --images 300 \
    --api-image-each 0.03 \
    --sweep-video 0:600:60

  # 4) Sweep a range of image usage and print a table
  python ai_media_breakeven.py \
    --subscription 48 \
    --api-video-per-sec 0.25 \
    --video-sec 180 \
    --sweep-images 0:1000:100 \
    --api-image-each 0.02

Notes:
- All costs are in the same currency (e.g., USD). Decimals are allowed.
- "Video seconds" means the sum of durations of all clips generated in the month.
- This tool is model-agnostic; plug in the per-second and per-image API rates you expect.
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Inputs:
    subscription: float                   # monthly flat subscription cost
    api_video_per_sec: float              # $ per second of generated video via API
    api_image_each: float                 # $ per generated image via API
    video_sec: Optional[float] = None     # seconds of video generated per month
    images: Optional[int] = None          # number of images generated per month


@dataclass
class Result:
    cost_subscription: float
    cost_api: float
    delta_api_minus_sub: float            # positive means API is more expensive
    is_subscription_better: bool


def compute_costs(inp: Inputs) -> Result:
    img = float(inp.images or 0)
    vid = float(inp.video_sec or 0.0)

    api_cost = img * inp.api_image_each + vid * inp.api_video_per_sec
    sub_cost = inp.subscription

    delta = api_cost - sub_cost
    is_sub_better = sub_cost < api_cost
    return Result(sub_cost, api_cost, delta, is_sub_better)


def breakeven_video_seconds(subscription: float, api_video_per_sec: float, images: int, api_image_each: float) -> Optional[float]:
    """
    Solve for video seconds V where subscription == API cost:
        subscription = api_video_per_sec * V + api_image_each * images
        => V = (subscription - api_image_each*images) / api_video_per_sec

    Returns None if api_video_per_sec <= 0 (undefined) or if the numerator is <= 0,
    meaning images alone already exceed subscription (subscription would always be cheaper).
    """
    if api_video_per_sec <= 0:
        return None
    numerator = subscription - (api_image_each * images)
    if numerator <= 0:
        return 0.0  # images alone exceed or match subscription; any video makes subscription better
    return numerator / api_video_per_sec


def parse_range(s: str) -> Tuple[float, float, float]:
    """
    Parse range strings like "start:end:step" (floats allowed).
    Example: "0:600:60" => (0, 600, 60)
    """
    try:
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError
        start, end, step = map(float, parts)
        if step <= 0:
            raise ValueError("Step must be > 0")
        return start, end, step
    except Exception:
        raise argparse.ArgumentTypeError('Range must be in "start:end:step" format, e.g., "0:600:60"')


def fmt_money(x: float) -> str:
    return f"${x:,.2f}"


def main():
    ap = argparse.ArgumentParser(description="AI Media Cost Break-even Calculator")
    ap.add_argument("--subscription", type=float, required=True, help="Monthly subscription cost (e.g., 48)")
    ap.add_argument("--api-video-per-sec", type=float, required=True, help="API cost per video second (e.g., 0.10)")
    ap.add_argument("--api-image-each", type=float, default=0.0, help="API cost per image (e.g., 0.05)")
    ap.add_argument("--video-sec", type=float, help="Total video seconds per month (optional)")
    ap.add_argument("--images", type=int, help="Total images per month (optional)")

    ap.add_argument("--show-breakeven", action="store_true", help="Compute and display break-even video seconds for given image usage & prices")
    ap.add_argument("--sweep-video", type=parse_range, help='Sweep a range of video seconds, e.g., "0:600:60"')
    ap.add_argument("--sweep-images", type=parse_range, help='Sweep a range of image counts, e.g., "0:1000:100"')

    args = ap.parse_args()

    inp = Inputs(
        subscription=args.subscription,
        api_video_per_sec=args.api_video_per_sec,
        api_image_each=args.api_image_each,
        video_sec=args.video_sec,
        images=args.images,
    )

    # Single-scenario report (if video or images provided)
    if args.video_sec is not None or args.images is not None:
        res = compute_costs(inp)
        print("\n=== Single Scenario ===")
        print(f"Subscription:            {fmt_money(res.cost_subscription)} / month")
        print(f"API (images+video):      {fmt_money(res.cost_api)} / month")
        print(f"Difference (API - Sub):  {fmt_money(res.delta_api_minus_sub)}")
        print(f"Cheaper option:          {'Subscription' if res.is_subscription_better else 'API or Tie'}")

    # Break-even (video seconds) for given image usage & prices
    if args.show_breakeven:
        images = args.images or 0
        bev = breakeven_video_seconds(args.subscription, args.api_video_per_sec, images, args.api_image_each)
        print("\n=== Break-even (Video Seconds) ===")
        if bev is None:
            print("Cannot compute break-even: api-video-per-sec must be > 0.")
        else:
            if bev == 0.0:
                print("Images alone meet/exceed the subscription cost; any additional video favors the subscription.")
            else:
                print(f"At {images} images/month and ${args.api_video_per_sec:.4f}/sec video,")
                print(f"break-even video usage is approximately: {bev:.2f} seconds/month")
                print("If you generate more video than this, the subscription is cheaper.")

    # Sweep video usage
    if args.sweep_video:
        start, end, step = args.sweep_video
        print("\n=== Sweep: Video Seconds ===")
        print("video_sec\tAPI_cost\tSub_cost\tCheaper")
        v = start
        while v <= end + 1e-9:
            inp.video_sec = v
            res = compute_costs(inp)
            cheaper = "Sub" if res.is_subscription_better else "API/Tie"
            print(f"{v:.0f}\t\t{fmt_money(res.cost_api)}\t{fmt_money(res.cost_subscription)}\t{cheaper}")
            v += step

    # Sweep image usage
    if args.sweep_images:
        start, end, step = args.sweep_images
        print("\n=== Sweep: Images ===")
        print("images\tAPI_cost\tSub_cost\tCheaper")
        i = start
        while i <= end + 1e-9:
            inp.images = int(i)
            res = compute_costs(inp)
            cheaper = "Sub" if res.is_subscription_better else "API/Tie"
            print(f"{int(i)}\t{fmt_money(res.cost_api)}\t{fmt_money(res.cost_subscription)}\t{cheaper}")
            i += step

    # If no scenario/sweep flags provided, print a quick help snippet
    if (
        args.video_sec is None and
        args.images is None and
        not args.show_breakeven and
        not args.sweep_video and
        not args.sweep_images
    ):
        print("\nNothing to compute. Try one of these:")
        print("  --video-sec 180 --images 200  (with --subscription and API prices)")
        print("  --show-breakeven")
        print('  --sweep-video "0:600:60"')
        print('  --sweep-images "0:1000:100"')


if __name__ == "__main__":
    main()
