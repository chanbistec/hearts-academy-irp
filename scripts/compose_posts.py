#!/usr/bin/env python3
"""
Compose final social media posts by overlaying text on generated images.
Creates ready-to-post assets with brand-consistent text overlays.

Usage:
    python scripts/compose_posts.py                    # Compose all
    python scripts/compose_posts.py --post launch-day  # Compose specific post
    python scripts/compose_posts.py --platform linkedin # Compose for platform
"""
import json
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent
ASSETS_DIR = ROOT / "assets" / "generated"
COMPOSED_DIR = ROOT / "assets" / "composed"
MANIFEST_PATH = ROOT / "assets" / "manifest.json"
FONT_PATH = Path("/tmp/roboto-bold.ttf")
FONT_REGULAR_PATH = Path("/tmp/roboto-regular.ttf")

# Brand colors
COLORS = {
    "bg_dark": "#0F172A",      # Dark navy
    "accent_blue": "#3B82F6",  # Electric blue
    "accent_orange": "#F97316",# Warm orange
    "text_white": "#FFFFFF",
    "text_light": "#E2E8F0",
    "text_muted": "#94A3B8",
    "overlay": (15, 23, 42, 180),  # Semi-transparent dark overlay
}

# Platform output sizes (pixels)
PLATFORM_SIZES = {
    "linkedin": (1200, 1200),
    "instagram-feed": (1080, 1080),
    "instagram-story": (1080, 1920),
    "instagram-carousel": (1080, 1080),
    "facebook": (1200, 630),
    "twitter": (1200, 675),
    "tiktok": (1080, 1920),
}

# Text overlay configurations for key posts
TEXT_OVERLAYS = {
    "launch-day": {
        "headline": "Industry Readiness\nProgram",
        "subline": "From classroom to production.\nIn 24 weeks.",
        "cta": "hearts.academy",
        "logo": "HEARTS ACADEMY",
    },
    "teaser-coming-soon": {
        "headline": "Something is\nchanging.",
        "subline": "March 31, 2026",
        "cta": "hearts.academy",
    },
    "teaser-tomorrow": {
        "headline": "Tomorrow.",
        "subline": "We change how you\nbecome an engineer.",
        "cta": "hearts.academy",
    },
    "urgency-oneweek": {
        "headline": "1 Week Left",
        "subline": "Applications close\nApril 20",
        "cta": "Apply → hearts.academy",
    },
    "urgency-48hrs": {
        "headline": "48 Hours",
        "subline": "Last chance to join\nCohort 1",
        "cta": "Apply → hearts.academy",
    },
    "urgency-final": {
        "headline": "Last Call",
        "subline": "Applications close\ntonight",
        "cta": "Apply now → hearts.academy",
    },
    "launch-ai": {
        "headline": "AI is here.\nAre you?",
        "subline": "Context Engineering\nMulti-Agent Orchestration",
        "cta": "hearts.academy",
    },
    "launch-overview": {
        "headline": "24 Weeks.\n5 Phases.\n1 Portfolio.",
        "subline": "",
        "cta": "hearts.academy",
    },
    "deep-rewards": {
        "headline": "Your output\ndetermines\nyour investment.",
        "subline": "Top 10% → 100% waiver\nTop 25% → 50% waiver",
        "cta": "hearts.academy",
    },
}


def get_font(size, bold=True):
    """Get font with fallback."""
    path = FONT_PATH if bold else FONT_REGULAR_PATH
    if path.exists():
        return ImageFont.truetype(str(path), size)
    # Fallback: try system fonts
    for fallback in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(fallback).exists():
            return ImageFont.truetype(fallback, size)
    return ImageFont.load_default()


def add_gradient_overlay(img, opacity=180):
    """Add a bottom-up gradient overlay for text readability."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    w, h = img.size
    # Gradient from bottom (dark) to 60% up (transparent)
    gradient_start = int(h * 0.4)
    for y in range(gradient_start, h):
        progress = (y - gradient_start) / (h - gradient_start)
        alpha = int(opacity * progress)
        draw.rectangle([(0, y), (w, y + 1)], fill=(15, 23, 42, alpha))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def compose_image(img_path, overlay_config, output_size, output_path):
    """Compose a final image with text overlay."""
    # Open and resize base image
    img = Image.open(img_path).convert("RGBA")
    img = img.resize(output_size, Image.LANCZOS)

    # Add gradient overlay
    img = add_gradient_overlay(img)

    draw = ImageDraw.Draw(img)
    w, h = output_size

    # Calculate font sizes based on image dimensions
    headline_size = int(min(w, h) * 0.08)
    subline_size = int(min(w, h) * 0.04)
    cta_size = int(min(w, h) * 0.035)
    logo_size = int(min(w, h) * 0.025)

    headline = overlay_config.get("headline", "")
    subline = overlay_config.get("subline", "")
    cta = overlay_config.get("cta", "")
    logo = overlay_config.get("logo", "HEARTS ACADEMY")

    # Position text in bottom portion
    y_cursor = int(h * 0.55)

    # Logo/brand at top-left
    if logo:
        font_logo = get_font(logo_size)
        draw.text((int(w * 0.05), int(h * 0.05)), logo, fill=COLORS["text_muted"], font=font_logo)

    # Headline
    if headline:
        font_headline = get_font(headline_size)
        draw.multiline_text(
            (int(w * 0.08), y_cursor),
            headline,
            fill=COLORS["text_white"],
            font=font_headline,
            spacing=int(headline_size * 0.3),
        )
        # Estimate height
        lines = headline.count("\n") + 1
        y_cursor += int(lines * headline_size * 1.3) + 20

    # Subline
    if subline:
        font_subline = get_font(subline_size, bold=False)
        draw.multiline_text(
            (int(w * 0.08), y_cursor),
            subline,
            fill=COLORS["text_light"],
            font=font_subline,
            spacing=int(subline_size * 0.4),
        )
        lines = subline.count("\n") + 1
        y_cursor += int(lines * subline_size * 1.4) + 30

    # CTA bar
    if cta:
        font_cta = get_font(cta_size)
        bbox = draw.textbbox((0, 0), cta, font=font_cta)
        cta_w = bbox[2] - bbox[0] + 40
        cta_h = bbox[3] - bbox[1] + 20
        cta_x = int(w * 0.08)
        cta_y = min(y_cursor, int(h * 0.88))

        # Draw rounded CTA button
        draw.rounded_rectangle(
            [(cta_x, cta_y), (cta_x + cta_w, cta_y + cta_h)],
            radius=8,
            fill=COLORS["accent_orange"],
        )
        draw.text(
            (cta_x + 20, cta_y + 10),
            cta,
            fill=COLORS["text_white"],
            font=font_cta,
        )

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(str(output_path), "PNG", quality=95)
    return output_path.stat().st_size


def main():
    parser = argparse.ArgumentParser(description="Compose final post images")
    parser.add_argument("--post", help="Specific post ID")
    parser.add_argument("--platform", help="Specific platform")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())

    composed = 0
    skipped = 0

    for filename, info in manifest.items():
        post_id = info["post"]
        platform = info["platform"]

        if args.post and post_id != args.post:
            continue
        if args.platform and platform != args.platform:
            continue

        # Only compose posts that have text overlay configs
        overlay_config = TEXT_OVERLAYS.get(post_id)
        if not overlay_config:
            continue

        src_path = ROOT / info["path"]
        if not src_path.exists():
            print(f"  ⚠️  Missing source: {src_path}")
            continue

        out_filename = f"{post_id}_{platform}_composed.png"
        output_path = COMPOSED_DIR / info["phase"] / out_filename
        output_size = PLATFORM_SIZES.get(platform, (1200, 1200))

        if output_path.exists() and not args.force:
            print(f"  ⏭️  Skip: {out_filename}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"  📋 Would compose: {out_filename}")
            continue

        print(f"  🖼️  Composing: {out_filename}...")
        try:
            size = compose_image(src_path, overlay_config, output_size, output_path)
            print(f"  ✅ Saved: {out_filename} ({size // 1024}KB)")
            composed += 1
        except Exception as e:
            print(f"  ❌ Error: {out_filename}: {e}")

    print(f"\n📊 Summary: {composed} composed, {skipped} skipped")


if __name__ == "__main__":
    main()
