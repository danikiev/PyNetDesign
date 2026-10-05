#!/usr/bin/env bash

# Linux/macOS uninstaller script for PyNetDesign
# Removes Conda environments whose name starts with "pnd", asking about each one.
# Run: ./uninstall.sh
#      ./uninstall.sh --yes    remove them without asking
# D. Anikiev, 2026-09-11

set -u

ENV_PATTERN="pnd"
ASSUME_YES=0

for arg in "$@"; do
    case "$arg" in
        -y|--yes)
            ASSUME_YES=1
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--yes]"
            echo "  -y, --yes   remove every matching environment without asking"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Try $(basename "$0") --help"
            exit 1
            ;;
    esac
done

if ! command -v conda >/dev/null 2>&1; then
    echo "Conda is not installed or not found in PATH."
    echo "Please install Conda (or Miniforge) and try again."
    exit 2
fi

CONDA_BASE="$(conda info --base 2>/dev/null)"
if [ -n "$CONDA_BASE" ] && [ -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1090
    source "$CONDA_BASE/etc/profile.d/conda.sh"
fi

# Collect environment names, matching the name only and not the path, so that an
# unrelated environment cannot be selected through a directory that contains "pnd".
ENVS="$(conda env list | awk -v pat="^${ENV_PATTERN}" '$1 ~ pat {print $1}')"

if [ -z "$ENVS" ]; then
    echo "No Conda environments whose name starts with \"$ENV_PATTERN\" were found."
    exit 0
fi

echo "Found the following Conda environments:"
echo "$ENVS" | sed 's/^/  /'
echo

REMOVED=0
while IFS= read -r ENV_NAME; do
    [ -z "$ENV_NAME" ] && continue

    if [ "$ASSUME_YES" -eq 1 ]; then
        CONFIRM="y"
    else
        read -r -p "Do you want to remove environment $ENV_NAME? (y/n): " CONFIRM
    fi

    case "$CONFIRM" in
        y|Y|yes|YES)
            echo "Deactivating any active Conda environment..."
            conda deactivate >/dev/null 2>&1 || true

            echo "Removing Conda environment $ENV_NAME..."
            conda remove -n "$ENV_NAME" --all --yes
            if [ $? -ne 0 ]; then
                echo "Failed to remove Conda environment $ENV_NAME."
                exit 3
            fi
            echo "Conda environment $ENV_NAME removed successfully."
            REMOVED=$((REMOVED + 1))
            ;;
        *)
            echo "Skipping Conda environment $ENV_NAME."
            ;;
    esac
done <<< "$ENVS"

echo
if [ "$REMOVED" -eq 0 ]; then
    echo "Nothing was removed."
else
    echo "Removed $REMOVED environment(s). Done!"
fi
