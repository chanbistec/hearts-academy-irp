#!/bin/bash
# Full content pipeline for Hearts Academy IRP campaign
# Usage:
#   ./scripts/pipeline.sh                     # Run full pipeline
#   ./scripts/pipeline.sh --phase launch      # Specific phase only
#   ./scripts/pipeline.sh --dry-run           # Preview without generating
#   ./scripts/pipeline.sh --images-only       # Only generate images
#   ./scripts/pipeline.sh --content-only      # Only generate text content
#   ./scripts/pipeline.sh --compose-only      # Only compose final assets

set -euo pipefail
cd "$(dirname "$0")/.."

PHASE=""
DRY_RUN=""
IMAGES_ONLY=false
CONTENT_ONLY=false
COMPOSE_ONLY=false
FORCE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --phase) PHASE="--phase $2"; shift 2;;
        --dry-run) DRY_RUN="--dry-run"; shift;;
        --images-only) IMAGES_ONLY=true; shift;;
        --content-only) CONTENT_ONLY=true; shift;;
        --compose-only) COMPOSE_ONLY=true; shift;;
        --force) FORCE="--force"; shift;;
        *) echo "Unknown option: $1"; exit 1;;
    esac
done

echo "╔══════════════════════════════════════════════════╗"
echo "║  Hearts Academy IRP — Content Pipeline           ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Ensure Roboto fonts are available
if [ ! -f /tmp/roboto-bold.ttf ]; then
    echo "⚠️  Roboto Bold font not found at /tmp/roboto-bold.ttf"
    echo "   Text overlays will use fallback font."
fi

# Step 1: Generate images
if [ "$CONTENT_ONLY" = false ] && [ "$COMPOSE_ONLY" = false ]; then
    echo "━━━ Step 1/3: Generating Images (Imagen 4) ━━━"
    python3 scripts/generate_images.py $PHASE $DRY_RUN $FORCE
    echo ""
fi

# Step 2: Generate text content
if [ "$IMAGES_ONLY" = false ] && [ "$COMPOSE_ONLY" = false ]; then
    echo "━━━ Step 2/3: Generating Content (Gemini) ━━━"
    python3 scripts/generate_content.py $PHASE $DRY_RUN $FORCE
    echo ""
fi

# Step 3: Compose final assets
if [ "$IMAGES_ONLY" = false ] && [ "$CONTENT_ONLY" = false ]; then
    echo "━━━ Step 3/3: Composing Final Assets ━━━"
    python3 scripts/compose_posts.py $PHASE $DRY_RUN $FORCE
    echo ""
fi

echo "╔══════════════════════════════════════════════════╗"
echo "║  Pipeline complete!                               ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "📁 Generated images:  assets/generated/"
echo "📝 Generated content: content/{platform}/"
echo "🖼️  Composed posts:   assets/composed/"
echo ""
echo "Next steps:"
echo "  1. Review content in content/{platform}/ folders"
echo "  2. Review composed images in assets/composed/"
echo "  3. Edit any drafts as needed"
echo "  4. Schedule posts using your preferred tool"
