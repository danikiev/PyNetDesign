#!/usr/bin/env bash

# Linux/macOS script for serving the PyNetDesign documentation locally.
# Rebuilds first, incrementally, so only the pages that changed are regenerated.
# Run: ./serve-docs.sh
#      ./serve-docs.sh --port 8080     serve on another port
#      ./serve-docs.sh --no-build      serve what is already built
#      ./serve-docs.sh --pdf           also build the PDF, so its download link works
# Extra Sphinx options can be passed through the SPHINXOPTS variable.
# D. Anikiev, 2026-09-11

set -u

PORT=8000
DO_BUILD=1
BUILD_PDF=0

while [ $# -gt 0 ]; do
    case "$1" in
        -n|--no-build)
            DO_BUILD=0
            shift
            ;;
        --pdf)
            BUILD_PDF=1
            shift
            ;;
        -p|--port)
            if [ $# -lt 2 ]; then
                echo "Missing value for $1"
                exit 1
            fi
            PORT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [-p PORT] [-n] [--pdf]"
            echo "  -p, --port PORT   port to serve on (default 8000)"
            echo "  -n, --no-build    skip the rebuild and serve what is already there"
            echo "      --pdf         also build the PDF, so its download link works"
            echo
            echo "Pass extra Sphinx options through SPHINXOPTS."
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Try $(basename "$0") --help"
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_DIR="$SCRIPT_DIR/docs/build/html"

# Build when asked, and also when there is nothing to serve yet
NEED_BUILD="$DO_BUILD"
if [ "$NEED_BUILD" -eq 0 ] && [ ! -f "$HTML_DIR/index.html" ]; then
    echo "No existing build found, building anyway..."
    NEED_BUILD=1
fi

if [ "$NEED_BUILD" -eq 1 ]; then
    # Delegate to build-docs so the build logic lives in one place
    BUILD_ARGS="--incremental"
    if [ "$BUILD_PDF" -eq 1 ]; then
        BUILD_ARGS="$BUILD_ARGS --pdf"
    fi
    # shellcheck disable=SC2086
    "$SCRIPT_DIR/build-docs.sh" $BUILD_ARGS
    if [ $? -ne 0 ]; then
        echo "Build failed, not serving."
        exit 1
    fi
fi

if [ ! -f "$HTML_DIR/index.html" ]; then
    echo "Documentation was not built: $HTML_DIR/index.html is missing."
    exit 3
fi

echo "##################################################################"
echo "Serving documentation at http://localhost:$PORT"
echo "Press Ctrl+C to stop."
cd "$HTML_DIR" || exit 4
python -m http.server "$PORT"
