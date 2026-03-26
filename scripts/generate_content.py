#!/usr/bin/env python3
"""
Generate social media content for Hearts Academy IRP campaign.
Uses Gemini to generate platform-specific copy based on brand voice and content plan.

Usage:
    python scripts/generate_content.py                     # Generate all
    python scripts/generate_content.py --phase launch      # Generate for specific phase
    python scripts/generate_content.py --platform linkedin  # Generate for specific platform
    python scripts/generate_content.py --post launch-day   # Generate a specific post
"""
import os
import json
import argparse
from pathlib import Path
from google import genai

ROOT = Path(__file__).parent.parent
ENV_PATH = ROOT / ".env"
CONTENT_DIR = ROOT / "content"
BRAND_VOICE = ROOT / "brand" / "voice-guide.md"

# Content definitions: each post maps to platform-specific specs
CONTENT_SPECS = {
    # === PHASE 1: PRE-LAUNCH TEASER ===
    "teaser-problem": {
        "phase": "teaser",
        "date": "2026-03-27",
        "topic": "The problem with CS degrees — gap between uni and industry",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 2000},
            "instagram": {"type": "story-caption", "max_chars": 200, "slides": 3},
        },
    },
    "teaser-thread": {
        "phase": "teaser",
        "date": "2026-03-28",
        "topic": "Why your CS degree isn't preparing you for 2026",
        "platforms": {
            "twitter": {"type": "thread", "tweets": 5, "max_chars": 280},
            "facebook": {"type": "post", "max_chars": 500},
        },
    },
    "teaser-poll": {
        "phase": "teaser",
        "date": "2026-03-29",
        "topic": "What's harder: getting a CS degree or landing your first dev job?",
        "platforms": {
            "linkedin": {"type": "poll", "options": 4},
            "instagram": {"type": "reel-script", "duration_sec": 30},
        },
    },
    "teaser-tomorrow": {
        "phase": "teaser",
        "date": "2026-03-30",
        "topic": "Tomorrow, we change how you become an engineer.",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 500},
            "instagram": {"type": "story-caption", "max_chars": 150},
            "twitter": {"type": "single", "max_chars": 280},
            "facebook": {"type": "post", "max_chars": 300},
        },
    },

    # === PHASE 2: LAUNCH WEEK ===
    "launch-day": {
        "phase": "launch",
        "date": "2026-03-31",
        "topic": "Official launch: Hearts Academy Industry Readiness Program",
        "key_points": [
            "24 weeks, 5 phases, 15-20hrs/week",
            "Real projects — ship production software",
            "AI-native curriculum (context engineering, multi-agent orchestration)",
            "Senior mentorship from experienced engineers",
            "8-10 cohort, performance-based pricing",
            "Apply: https://forms.office.com/r/kM2prJrNgg",
            "Applications close April 20",
            "Website: https://www.hearts.academy",
        ],
        "platforms": {
            "linkedin": {"type": "long-post", "max_chars": 3000},
            "instagram": {"type": "carousel-captions", "slides": 8, "max_chars": 2200},
            "twitter": {"type": "thread", "tweets": 8, "max_chars": 280},
            "facebook": {"type": "post", "max_chars": 1000},
            "tiktok": {"type": "video-script", "duration_sec": 45},
        },
    },
    "launch-pillars": {
        "phase": "launch",
        "date": "2026-04-01",
        "topic": "What you get: 6 pillars (Toastmasters, mentoring, industry talks, real projects, code crunch, placement)",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 2000},
            "instagram": {"type": "story-series", "slides": 6},
        },
    },
    "launch-ai": {
        "phase": "launch",
        "date": "2026-04-02",
        "topic": "AI curriculum spotlight — AI is here. Are you?",
        "key_points": [
            "Context engineering",
            "Multi-agent orchestration",
            "AI-powered teams",
            "Not just prompt engineering",
        ],
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 2000},
            "twitter": {"type": "thread", "tweets": 5, "max_chars": 280},
            "tiktok": {"type": "video-script", "duration_sec": 30},
        },
    },
    "launch-testimonial": {
        "phase": "launch",
        "date": "2026-04-03",
        "topic": "Jayath De Silva testimonial — from intern to software engineer",
        "quote": "The supportive, collaborative environment, along with the trust and mentorship I received, played a key role in my development",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1500},
            "instagram": {"type": "feed-caption", "max_chars": 2200},
            "facebook": {"type": "post", "max_chars": 800},
        },
    },
    "launch-overview": {
        "phase": "launch",
        "date": "2026-04-04",
        "topic": "24 weeks. 5 phases. 1 portfolio.",
        "platforms": {
            "instagram": {"type": "reel-script", "duration_sec": 30},
        },
    },
    "launch-founder": {
        "phase": "launch",
        "date": "2026-04-05",
        "topic": "Why we built Hearts Academy — founder story",
        "platforms": {
            "linkedin": {"type": "article", "max_chars": 5000},
        },
    },

    # === PHASE 3: SOCIAL PROOF & DEEP DIVES ===
    "deep-phases": {
        "phase": "deep-dive",
        "date": "2026-04-07",
        "topic": "Phase-by-phase breakdown of the 24-week program",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 2000},
            "instagram": {"type": "carousel-captions", "slides": 10, "max_chars": 2200},
        },
    },
    "deep-rewards": {
        "phase": "deep-dive",
        "date": "2026-04-08",
        "topic": "Performance rewards — top 10% get 100% fee waiver",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1500},
            "twitter": {"type": "thread", "tweets": 5, "max_chars": 280},
        },
    },
    "deep-context-eng": {
        "phase": "deep-dive",
        "date": "2026-04-09",
        "topic": "What is context engineering? Why it matters in the agentic era.",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 2000},
            "tiktok": {"type": "video-script", "duration_sec": 45},
        },
    },
    "deep-faq": {
        "phase": "deep-dive",
        "date": "2026-04-10",
        "topic": "FAQ roundup — Can I work while studying? Do I need to code? What's the fee?",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 2000},
            "instagram": {"type": "story-qa", "questions": 5},
        },
    },
    "deep-softskills": {
        "phase": "deep-dive",
        "date": "2026-04-11",
        "topic": "Toastmasters and soft skills — what separates great engineers from good ones",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1500},
            "facebook": {"type": "post", "max_chars": 800},
        },
    },
    "deep-dayinlife": {
        "phase": "deep-dive",
        "date": "2026-04-12",
        "topic": "A day in the life of an IRP student (aspirational)",
        "platforms": {
            "instagram": {"type": "reel-script", "duration_sec": 45},
        },
    },

    # === PHASE 4: URGENCY & CLOSE ===
    "urgency-oneweek": {
        "phase": "urgency",
        "date": "2026-04-14",
        "topic": "1 WEEK LEFT — Applications close April 20",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1000},
            "instagram": {"type": "story-caption", "max_chars": 150},
            "facebook": {"type": "post", "max_chars": 500},
            "twitter": {"type": "single", "max_chars": 280},
        },
    },
    "urgency-process": {
        "phase": "urgency",
        "date": "2026-04-15",
        "topic": "What happens after you apply — process transparency",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1500},
            "instagram": {"type": "story-series", "slides": 4},
        },
    },
    "urgency-reshare": {
        "phase": "urgency",
        "date": "2026-04-16",
        "topic": "Re-share testimonial + spots filling up",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1000},
            "twitter": {"type": "single", "max_chars": 280},
        },
    },
    "urgency-outcomes": {
        "phase": "urgency",
        "date": "2026-04-17",
        "topic": "What you'll have in 6 months — tangible outcomes",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1500},
            "tiktok": {"type": "video-script", "duration_sec": 30},
        },
    },
    "urgency-48hrs": {
        "phase": "urgency",
        "date": "2026-04-18",
        "topic": "48 hours left — final push with program recap",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1000},
            "instagram": {"type": "feed-caption", "max_chars": 1000},
            "facebook": {"type": "post", "max_chars": 500},
            "twitter": {"type": "single", "max_chars": 280},
        },
    },
    "urgency-lastday-eve": {
        "phase": "urgency",
        "date": "2026-04-19",
        "topic": "LAST DAY TOMORROW",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 800},
            "instagram": {"type": "story-caption", "max_chars": 150},
            "twitter": {"type": "single", "max_chars": 280},
        },
    },
    "urgency-final": {
        "phase": "urgency",
        "date": "2026-04-20",
        "topic": "Last chance. Applications close tonight.",
        "platforms": {
            "linkedin": {"type": "text-post", "max_chars": 1000},
            "instagram": {"type": "feed-caption", "max_chars": 1000},
            "facebook": {"type": "post", "max_chars": 500},
            "twitter": {"type": "single", "max_chars": 280},
            "tiktok": {"type": "video-script", "duration_sec": 30},
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
    raise ValueError("GEMINI_API_KEY not found")


def load_brand_voice():
    if BRAND_VOICE.exists():
        return BRAND_VOICE.read_text()
    return ""


def build_prompt(post_id, spec, platform, platform_spec, brand_voice):
    """Build a generation prompt for a specific post + platform."""
    content_type = platform_spec["type"]
    topic = spec["topic"]
    key_points = spec.get("key_points", [])
    quote = spec.get("quote", "")
    date = spec["date"]

    prompt = f"""You are a social media content creator for Hearts Academy, a tech education program in Sri Lanka.

BRAND VOICE:
{brand_voice}

TASK: Create a {content_type} for {platform.upper()} about: {topic}

DATE: {date}
APPLICATION LINK: https://forms.office.com/r/kM2prJrNgg
WEBSITE: https://www.hearts.academy
APPLICATIONS CLOSE: April 20, 2026

"""
    if key_points:
        prompt += "KEY POINTS TO INCLUDE:\n" + "\n".join(f"- {p}" for p in key_points) + "\n\n"
    if quote:
        prompt += f'TESTIMONIAL QUOTE: "{quote}" — Jayath De Silva, Intern Software Engineer → Software Engineer\n\n'

    # Platform-specific instructions
    if content_type == "thread":
        tweets = platform_spec.get("tweets", 5)
        prompt += f"""FORMAT: Twitter/X thread with {tweets} tweets.
- Each tweet under 280 characters
- First tweet is the hook
- Last tweet has the CTA + link
- Number each tweet (1/{tweets}, 2/{tweets}, etc.)
- Use relevant hashtags sparingly (1-2 per tweet)
"""
    elif content_type == "carousel-captions":
        slides = platform_spec.get("slides", 8)
        prompt += f"""FORMAT: Instagram carousel with {slides} slides.
- Write the main caption (under {platform_spec.get('max_chars', 2200)} chars)
- Then write text for each slide (short, punchy, 1-2 sentences per slide)
- Include hashtags at the end (10-15 relevant ones)
- Include CTA to apply
"""
    elif content_type in ("long-post", "text-post"):
        prompt += f"""FORMAT: {platform.capitalize()} post (max {platform_spec.get('max_chars', 2000)} characters).
- Hook in first 2 lines (shown in preview)
- Use line breaks for readability
- Include 3-5 relevant hashtags
- End with clear CTA
"""
    elif content_type == "video-script":
        duration = platform_spec.get("duration_sec", 30)
        prompt += f"""FORMAT: TikTok/Reels video script ({duration} seconds).
- HOOK (first 3 seconds): attention grabber
- BODY: key message, keep it conversational
- CTA: what to do next
- Include suggested on-screen text
- Include suggested background music mood
"""
    elif content_type == "reel-script":
        duration = platform_spec.get("duration_sec", 30)
        prompt += f"""FORMAT: Instagram Reel script ({duration} seconds).
- HOOK (first 3 seconds)
- BODY with visual directions
- CTA overlay
- Suggested music mood
"""
    elif content_type == "poll":
        prompt += f"""FORMAT: LinkedIn poll.
- Write the poll question
- Write 4 options
- Add context text above the poll (2-3 sentences)
"""
    elif content_type in ("story-caption", "story-series", "story-qa"):
        slides = platform_spec.get("slides", platform_spec.get("questions", 3))
        prompt += f"""FORMAT: Instagram story series ({slides} slides).
- Short text per slide (under 100 chars)
- Include sticker suggestions (poll, question, countdown)
- Mobile-first, vertical
"""
    elif content_type == "article":
        prompt += f"""FORMAT: LinkedIn article (up to {platform_spec.get('max_chars', 5000)} characters).
- Compelling headline
- Personal/founder perspective
- Why this program exists
- What makes it different
- End with CTA
"""
    elif content_type == "single":
        prompt += f"""FORMAT: Single tweet (max 280 characters).
- Punchy, direct
- Include link if space allows
- 1-2 hashtags max
"""
    else:
        prompt += f"""FORMAT: {platform.capitalize()} {content_type} (max {platform_spec.get('max_chars', 500)} chars).
- Platform-appropriate tone
- Include CTA
"""

    prompt += "\nGenerate the content now. Output ONLY the ready-to-post content, no meta-commentary."
    return prompt


def generate_content(client, prompt):
    """Generate content via Gemini."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text


def main():
    parser = argparse.ArgumentParser(description="Generate IRP campaign content")
    parser.add_argument("--phase", choices=["teaser", "launch", "deep-dive", "urgency"])
    parser.add_argument("--platform", choices=["linkedin", "instagram", "twitter", "facebook", "tiktok"])
    parser.add_argument("--post", help="Specific post ID")
    parser.add_argument("--force", action="store_true", help="Regenerate existing content")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()

    api_key = get_api_key()
    client = genai.Client(api_key=api_key)
    brand_voice = load_brand_voice()

    total = 0
    generated = 0
    skipped = 0

    for post_id, spec in CONTENT_SPECS.items():
        if args.phase and spec["phase"] != args.phase:
            continue
        if args.post and post_id != args.post:
            continue

        for platform, platform_spec in spec["platforms"].items():
            if args.platform and platform != args.platform:
                continue

            total += 1
            filename = f"{spec['date']}_{post_id}.md"
            output_path = CONTENT_DIR / platform / filename

            if output_path.exists() and not args.force:
                print(f"  ⏭️  Skip: {platform}/{filename}")
                skipped += 1
                continue

            if args.dry_run:
                print(f"  📋 Would generate: {platform}/{filename}")
                continue

            print(f"  ✍️  Generating: {platform}/{filename}...")
            prompt = build_prompt(post_id, spec, platform, platform_spec, brand_voice)

            try:
                content = generate_content(client, prompt)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write with metadata header
                header = f"""---
post_id: {post_id}
platform: {platform}
type: {platform_spec['type']}
date: {spec['date']}
phase: {spec['phase']}
topic: "{spec['topic']}"
status: draft
---

"""
                output_path.write_text(header + content)
                print(f"  ✅ Saved: {platform}/{filename}")
                generated += 1
            except Exception as e:
                print(f"  ❌ Error: {platform}/{filename}: {e}")

    print(f"\n📊 Summary: {generated} generated, {skipped} skipped (of {total} total)")


if __name__ == "__main__":
    main()
