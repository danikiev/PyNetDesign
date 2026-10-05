#!/usr/bin/env bash

# Linux/macOS installer script for PyNetDesign
# Creates the Conda environment from environment.yml and installs the package.
# environment.yml pins only the interpreter; the dependencies come from pyproject.toml,
# as runtime requirements plus the optional "dev" and "docs" groups.
# Run: ./install.sh
#      ./install.sh --dev    install the development tools without being asked
# D. Anikiev, 2026-09-11

set -u

ENV_NAME="pnd"
ENV_YAML="environment.yml"
PACKAGE_NAME="pynetdesign"
WITH_DEV=""

for arg in "$@"; do
    case "$arg" in
        --dev)
            WITH_DEV="y"
            ;;
        --no-dev)
            WITH_DEV="n"
            ;;
        -h|--help)
            echo "Usage: $(basename "$0") [--dev|--no-dev]"
            echo "  --dev      install the development tools (tests, documentation)"
            echo "  --no-dev   install the runtime dependencies only"
            echo "Without a flag the script asks."
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

if [ ! -f "$ENV_YAML" ]; then
    echo "$ENV_YAML not found in the current directory."
    echo "Please run this script from the repository root."
    exit 3
fi

if [ -z "$WITH_DEV" ]; then
    echo "PyNetDesign will be installed into the Conda environment \"$ENV_NAME\"."
    echo
    echo "The development tools add pytest, a Jupyter stack and the Sphinx"
    echo "toolchain for building the documentation locally."
    read -r -p "Install the development tools as well? (y/n): " WITH_DEV
fi

# Note: the variable must not be named PIP_something. pip reads PIP_<OPTION> from the
# environment, so e.g. PIP_TARGET would silently become pip's --target option.
case "$WITH_DEV" in
    y|Y|yes|YES)
        INSTALL_SPEC=".[dev,docs]"
        echo "Installing with the development tools."
        ;;
    *)
        INSTALL_SPEC="."
        echo "Installing the runtime dependencies only."
        ;;
esac

echo "Creating Conda environment $ENV_NAME from $ENV_YAML..."
conda env create -f "$ENV_YAML" -n "$ENV_NAME"
if [ $? -ne 0 ]; then
    echo "Failed to create Conda environment $ENV_NAME."
    exit 4
fi

echo "Conda environments:"
conda env list

CONDA_BASE="$(conda info --base 2>/dev/null)"
if [ -z "$CONDA_BASE" ] || [ ! -f "$CONDA_BASE/etc/profile.d/conda.sh" ]; then
    echo "Could not locate conda.sh for environment activation."
    exit 5
fi

echo "Activating Conda environment $ENV_NAME..."
# shellcheck disable=SC1090
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"
if [ $? -ne 0 ]; then
    echo "Failed to activate Conda environment $ENV_NAME."
    exit 5
fi

echo "Installing $PACKAGE_NAME..."
pip install -e "$INSTALL_SPEC"
if [ $? -ne 0 ]; then
    echo "Failed to install $PACKAGE_NAME."
    exit 6
fi

echo "Python version:"
python --version

echo "Python path:"
command -v python

echo "Done!"
echo "Activate the environment in a new shell with: conda activate $ENV_NAME"
