#!/usr/bin/env bash

# Linux/macOS script for building the PyNetDesign documentation.
# Run: ./build-docs.sh
#      ./build-docs.sh --incremental   rebuild only what changed
#      ./build-docs.sh --pdf           also build the PDF and place it in the HTML tree
# Extra Sphinx options can be passed through the SPHINXOPTS variable, e.g.
#      SPHINXOPTS="-D plot_gallery=0" ./build-docs.sh    build without running examples
# Use ./serve-docs.sh to view the result in a browser.
# Requires the docs extra: pip install -e ".[docs]"
# The PDF additionally requires a LaTeX installation providing lualatex and latexmk.
# D. Anikiev, 2026-09-11

set -u

CLEAN=1
BUILD_PDF=0
for arg in "$@"; do
    case "$arg" in
        -i|--incremental)
            CLEAN=0
            ;;
        --pdf)
            BUILD_PDF=1
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--incremental] [--pdf]"
            echo "  -i, --incremental   skip the clean and rebuild only what changed"
            echo "      --pdf           also build the PDF into docs/build/html/_static"
            echo
            echo "Pass extra Sphinx options through SPHINXOPTS."
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Try $(basename "$0") --help"
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/docs/source"
BUILD_DIR="$SCRIPT_DIR/docs/build"
PDF_NAME="pynetdesign.pdf"

if [ ! -f "$SOURCE_DIR/conf.py" ]; then
    echo "Sphinx configuration not found: $SOURCE_DIR/conf.py"
    exit 1
fi

if ! python -c "import sphinx" >/dev/null 2>&1; then
    echo "Sphinx is not installed in the active environment."
    echo "Install the documentation tools with: pip install -e \".[docs]\""
    exit 2
fi

if [ "$BUILD_PDF" -eq 1 ]; then
    for tool in lualatex latexmk; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            echo "$tool not found in PATH, which is required for the PDF build."
            echo "Install a LaTeX distribution, or drop --pdf to build the HTML only."
            exit 2
        fi
    done
fi

if [ "$CLEAN" -eq 1 ]; then
    echo "##################################################################"
    echo "Cleaning..."
    python -m sphinx -M clean "$SOURCE_DIR" "$BUILD_DIR"
    if [ $? -ne 0 ]; then
        echo "Error while cleaning!"
        exit 1
    fi
fi

echo "##################################################################"
echo "Building HTML..."
# shellcheck disable=SC2086
python -m sphinx -M html "$SOURCE_DIR" "$BUILD_DIR" ${SPHINXOPTS:-}
if [ $? -ne 0 ]; then
    echo "Error during HTML build process!"
    exit 1
fi

if [ "$BUILD_PDF" -eq 1 ]; then
    echo "##################################################################"
    echo "Generating LaTeX..."
    # shellcheck disable=SC2086
    python -m sphinx -M latex "$SOURCE_DIR" "$BUILD_DIR" ${SPHINXOPTS:-}
    if [ $? -ne 0 ]; then
        echo "Error while generating LaTeX!"
        exit 1
    fi

    echo "##################################################################"
    echo "Building PDF..."
    # latexmk reads the latexmkrc that Sphinx writes next to the .tex, which binds the
    # engine (lualatex) and the python.ist index style, so -pdf resolves to lualatex here.
    (cd "$BUILD_DIR/latex" && latexmk -pdf -dvi- -ps- -interaction=nonstopmode -halt-on-error "${PDF_NAME%.pdf}.tex")
    if [ $? -ne 0 ] || [ ! -f "$BUILD_DIR/latex/$PDF_NAME" ]; then
        echo "Error during PDF build process!"
        echo "See $BUILD_DIR/latex/${PDF_NAME%.pdf}.log for the LaTeX output."
        exit 1
    fi

    echo "##################################################################"
    echo "Copying the PDF into the HTML tree..."
    mkdir -p "$BUILD_DIR/html/_static"
    cp "$BUILD_DIR/latex/$PDF_NAME" "$BUILD_DIR/html/_static/$PDF_NAME"
    if [ $? -ne 0 ]; then
        echo "Error while copying the PDF!"
        exit 2
    fi
fi

echo "##################################################################"
echo "Documentation built in docs/build/html"
if [ "$BUILD_PDF" -eq 1 ]; then
    echo "PDF available at docs/build/html/_static/$PDF_NAME"
else
    echo "The PDF was not built; pass --pdf to build it as well."
fi
echo "Open docs/build/html/index.html, or run ./serve-docs.sh to serve it."
