#!/usr/bin/env python3
"""
Generate social media images for Hearts Academy IRP campaign using Imagen 4.
Generates platform-specific images with correct aspect ratios.

Usage:
    python scripts/generate_images.py                    # Generate all
    python scripts/generate_images.py --phase launch     # Generate for specific phase
    python scripts/generate_images.py --platform linkedin # Generate for specific platform
    python scripts/generate_images.py --post launch-day  # Generate a specific post
"""
import os
import sys
import json
import argparse
from pathlib import Path
from google import genai

ROOT = Path(__file__).parent.parent
ENV_PATH = ROOT / ".env"
ASSETS_DIR = ROOT / "assets" / "generated"
MANIFEST_PATH = ROOT / "assets" / "manifest.json"

# Platform aspect ratios
PLATFORM_RATIOS = {
    "linkedin": "1:1",        # Square posts work best
    "instagram-feed": "1:1",  # Square feed posts
    "instagram-story": "9:16",# Vertical stories/reels
    "instagram-carousel": "1:1",
    "facebook": "16:9",       # Landscape
    "twitter": "16:9",        # Landscape
    "tiktok": "9:16",         # Vertical
}

# Brand style prefix for all prompts
BRAND_STYLE = (
    "Modern, clean, professional tech education aesthetic. "
    "Dark navy/charcoal background with vibrant accent colors (electric blue, warm orange). "
    "Minimalist design, subtle code/tech elements. "
    "Premium feel, not generic stock. No text overlays. "
)

# Image definitions organized by phase and post
IMAGE_SPECS = {
    # === PHASE 1: PRE-LAUNCH TEASER (Mar 27-30) ===
    "teaser-problem": {
        "phase": "teaser",
        "desc": "The gap between CS degree and industry",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Split composition: left side shows a graduation cap and textbook in muted grey tones, right side shows a glowing laptop with deployed code in vibrant blue and orange. Visual metaphor for the gap between education and industry. Professional, thought-provoking.",
            "instagram-story": f"{BRAND_STYLE}Vertical split: top half shows faded classroom/textbook imagery, bottom half shows vibrant real-world coding/deployment. Dramatic lighting transition from grey to colorful. Eye-catching for stories.",
        },
    },
    "teaser-coming-soon": {
        "phase": "teaser",
        "desc": "Something is coming teaser",
        "platforms": {
            "instagram-story": f"{BRAND_STYLE}Mysterious vertical composition, dark background with a single glowing code terminal screen, particles of light emanating from it, futuristic feel, anticipation and excitement, minimal and cinematic.",
            "linkedin": f"{BRAND_STYLE}Dark minimal composition with a subtle glowing circuit board pattern forming a forward arrow shape, sense of anticipation and innovation, professional and intriguing.",
        },
    },
    "teaser-poll": {
        "phase": "teaser",
        "desc": "Degree vs first job difficulty",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Two paths diverging: one path labeled with academic symbols (books, graduation cap), the other with industry symbols (laptop, server, rocket). Crossroads metaphor, professional illustration style.",
        },
    },

    # === PHASE 2: LAUNCH WEEK (Mar 31 - Apr 6) ===
    "launch-day": {
        "phase": "launch",
        "desc": "Official launch announcement",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Dramatic launch visual: a rocket or upward trajectory made of code lines and circuit patterns, bursting through clouds into clear sky. Electric blue and orange energy trails. Professional, aspirational, exciting.",
            "instagram-feed": f"{BRAND_STYLE}Square composition launch visual: abstract upward-moving energy burst made of code fragments and neural network patterns, dark background with electric blue and warm orange glow, sense of launch and beginning.",
            "instagram-carousel": f"{BRAND_STYLE}Clean square background for carousel slide: dark navy gradient with subtle geometric code patterns, space for text overlay, professional and modern, tech education feel.",
            "facebook": f"{BRAND_STYLE}Wide landscape launch banner: panoramic view of a modern tech workspace transforming from a traditional classroom, gradient from grey to vibrant, symbolizing transformation, wide composition.",
            "twitter": f"{BRAND_STYLE}Wide landscape: dynamic burst of energy representing launch, code particles and light rays, electric blue and orange on dark background, impactful and shareable.",
            "tiktok": f"{BRAND_STYLE}Vertical dramatic composition: student silhouette standing at the edge of a futuristic tech landscape, looking forward at glowing opportunities (code, servers, AI), aspirational and cinematic.",
        },
    },
    "launch-pillars": {
        "phase": "launch",
        "desc": "6 pillars of the program",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Six interconnected hexagonal nodes forming a honeycomb pattern, each subtly representing: speaking, mentoring, industry talks, real projects, hackathons, placement. Glowing connections between them, professional infographic feel.",
            "instagram-carousel": f"{BRAND_STYLE}Clean square background for carousel: dark navy gradient with subtle hexagonal pattern, space for text overlay, one pillar per slide, professional tech education aesthetic.",
        },
    },
    "launch-ai": {
        "phase": "launch",
        "desc": "AI curriculum spotlight",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}AI and neural network visualization: multiple AI agents collaborating, represented as glowing interconnected nodes with data flowing between them. Context engineering visual metaphor. Futuristic but accessible.",
            "twitter": f"{BRAND_STYLE}Wide landscape: modern AI agent orchestration visualization, multiple glowing AI entities working together, data streams flowing, tech stack icons subtly visible, professional.",
            "tiktok": f"{BRAND_STYLE}Vertical: dramatic AI visualization, a person working alongside glowing AI agents on screens, futuristic developer workspace, cinematic lighting, aspirational.",
        },
    },
    "launch-testimonial": {
        "phase": "launch",
        "desc": "Jayath De Silva testimonial",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Professional testimonial background: abstract upward growth trajectory, a path from one level to another (intern to engineer metaphor), warm orange and blue gradient, clean and inspiring.",
            "instagram-feed": f"{BRAND_STYLE}Square testimonial background: dark clean backdrop with subtle upward-moving light particles, warm and professional, space for quote overlay, inspiring growth feel.",
            "facebook": f"{BRAND_STYLE}Wide landscape testimonial background: journey metaphor with path leading from shadows into light, professional growth symbolism, warm tones.",
        },
    },
    "launch-overview": {
        "phase": "launch",
        "desc": "24 weeks, 5 phases, 1 portfolio",
        "platforms": {
            "instagram-story": f"{BRAND_STYLE}Vertical timeline visual: 5 ascending steps/phases glowing progressively brighter from bottom to top, dark background, each step connected by flowing code lines, culminating in a glowing portfolio at the top.",
        },
    },

    # === PHASE 3: SOCIAL PROOF & DEEP DIVES (Apr 7-13) ===
    "deep-phases": {
        "phase": "deep-dive",
        "desc": "5 phases breakdown",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Five connected ascending platforms or stages, each progressively more complex and vibrant, representing program phases from foundation to deployment. Pipeline visual with flowing data.",
            "instagram-carousel": f"{BRAND_STYLE}Clean dark background for carousel slides: each with a distinct subtle glow color representing a program phase, minimal geometric patterns, space for text overlay.",
        },
    },
    "deep-rewards": {
        "phase": "deep-dive",
        "desc": "Performance-based pricing",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Podium or achievement visual: ascending bars or trophies representing performance tiers, top performers glowing brightest, reward and meritocracy concept, professional and motivating.",
            "twitter": f"{BRAND_STYLE}Wide landscape: performance reward concept, ascending chart or podium with glowing top tier, orange and blue accents, achievement feel.",
        },
    },
    "deep-context-eng": {
        "phase": "deep-dive",
        "desc": "What is context engineering",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Abstract visualization of context engineering: layers of data and context being structured and fed into an AI system, like a sophisticated pipeline, glowing data flows, technical but beautiful.",
            "tiktok": f"{BRAND_STYLE}Vertical: developer at a futuristic workstation with holographic AI context windows floating around them, sci-fi but grounded in reality, cinematic.",
        },
    },
    "deep-faq": {
        "phase": "deep-dive",
        "desc": "FAQ roundup",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Clean Q&A concept: floating question mark shapes dissolving into answer checkmarks, transformation visual, professional blue and orange on dark background.",
            "instagram-story": f"{BRAND_STYLE}Vertical Q&A visual: large glowing question mark with smaller answered questions floating around it, interactive feel, dark background with blue glow.",
        },
    },
    "deep-softskills": {
        "phase": "deep-dive",
        "desc": "Toastmasters and soft skills",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Confident speaker silhouette at a podium with audience, warm orange spotlight, professional presentation setting, Toastmasters energy, growth and confidence.",
            "facebook": f"{BRAND_STYLE}Wide landscape: group of professionals in a modern meeting room, collaborative energy, warm lighting, presentation screen visible, soft skills development vibe.",
        },
    },

    # === PHASE 4: URGENCY & CLOSE (Apr 14-20) ===
    "urgency-oneweek": {
        "phase": "urgency",
        "desc": "1 week left countdown",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Countdown clock concept: hourglass or timer with glowing sand/particles running out, urgent but not panic, professional urgency, orange and blue accents.",
            "instagram-story": f"{BRAND_STYLE}Vertical countdown: dramatic hourglass with glowing particles, timer running down, dark background with urgent orange glow, eye-catching.",
            "facebook": f"{BRAND_STYLE}Wide countdown banner: timer or calendar concept with April 20 highlighted and glowing, professional urgency.",
            "twitter": f"{BRAND_STYLE}Wide landscape: clean countdown concept, calendar with date circled in glowing orange, professional urgency feel.",
        },
    },
    "urgency-outcomes": {
        "phase": "urgency",
        "desc": "What you'll have in 6 months",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Before/after transformation: empty profile transforming into rich developer portfolio with deployed projects, GitHub contributions, professional growth visualization.",
            "tiktok": f"{BRAND_STYLE}Vertical: split screen concept, left side nervous student, right side confident developer with glowing portfolio and code, transformation visual, cinematic.",
        },
    },
    "urgency-final": {
        "phase": "urgency",
        "desc": "Last chance - applications close",
        "platforms": {
            "linkedin": f"{BRAND_STYLE}Closing door concept: a glowing doorway of opportunity slowly closing, particles of light streaming through, last chance energy, professional and dramatic.",
            "instagram-feed": f"{BRAND_STYLE}Square: glowing portal or doorway with closing motion, urgent but aspirational, last chance to step through, dramatic lighting.",
            "instagram-story": f"{BRAND_STYLE}Vertical: dramatic closing door of light, urgent orange glow, particles, final call energy, dark cinematic.",
            "facebook": f"{BRAND_STYLE}Wide landscape: closing window of opportunity visual, dramatic and urgent, professional.",
            "twitter": f"{BRAND_STYLE}Wide landscape: door closing concept, final chance energy, glowing portal narrowing, professional.",
            "tiktok": f"{BRAND_STYLE}Vertical: dramatic closing portal, cinematic urgency, final call, aspirational and dramatic.",
        },
    },
}


def get_api_key():
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                return line.split("=", 1)[1].strip()
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    raise ValueError("GEMINI_API_KEY not found in .env or environment")


def generate_image(client, prompt, aspect_ratio, output_path):
    """Generate a single image via Imagen 4."""
    response = client.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=prompt,
        config=genai.types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
        ),
    )
    if response.generated_images:
        img_bytes = response.generated_images[0].image.image_bytes
        output_path.write_bytes(img_bytes)
        return len(img_bytes)
    return 0


def load_manifest():
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text())
    return {}


def save_manifest(manifest):
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Generate IRP campaign images")
    parser.add_argument("--phase", choices=["teaser", "launch", "deep-dive", "urgency"], help="Generate for specific phase")
    parser.add_argument("--platform", help="Generate for specific platform (e.g., linkedin, instagram-feed)")
    parser.add_argument("--post", help="Generate for specific post ID (e.g., launch-day)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if image exists")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling API")
    args = parser.parse_args()

    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    manifest = load_manifest()

    total = 0
    generated = 0
    skipped = 0
    errors = 0

    for post_id, spec in IMAGE_SPECS.items():
        # Filter by phase
        if args.phase and spec["phase"] != args.phase:
            continue
        # Filter by post
        if args.post and post_id != args.post:
            continue

        for platform, prompt in spec["platforms"].items():
            # Filter by platform
            if args.platform and platform != args.platform:
                continue

            total += 1
            ratio = PLATFORM_RATIOS.get(platform, "1:1")
            filename = f"{post_id}_{platform}.png"
            output_path = ASSETS_DIR / spec["phase"] / filename

            # Skip if already generated (unless --force)
            if output_path.exists() and not args.force:
                print(f"  ⏭️  Skip (exists): {filename}")
                skipped += 1
                continue

            if args.dry_run:
                print(f"  📋 Would generate: {filename} ({ratio})")
                continue

            output_path.parent.mkdir(parents=True, exist_ok=True)
            print(f"  🎨 Generating: {filename} ({ratio})...")

            try:
                size = generate_image(client, prompt, ratio, output_path)
                if size:
                    print(f"  ✅ Saved: {filename} ({size // 1024}KB)")
                    manifest[filename] = {
                        "post": post_id,
                        "platform": platform,
                        "phase": spec["phase"],
                        "ratio": ratio,
                        "size_kb": size // 1024,
                        "path": str(output_path.relative_to(ROOT)),
                    }
                    generated += 1
                else:
                    print(f"  ❌ No image returned: {filename}")
                    errors += 1
            except Exception as e:
                print(f"  ❌ Error: {filename}: {e}")
                errors += 1

    save_manifest(manifest)
    print(f"\n📊 Summary: {generated} generated, {skipped} skipped, {errors} errors (of {total} total)")


if __name__ == "__main__":
    main()
