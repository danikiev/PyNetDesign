<h1 align="center">
  <img src="docs/source/_static/pynetdesign-logo.svg" alt="PyNetDesign logo" width="520">
</h1><br>

[![DOI](https://zenodo.org/badge/958300487.svg)](https://zenodo.org/badge/latestdoi/958300487)
[![Pytest](https://github.com/danikiev/PyNetDesign/actions/workflows/pytest.yml/badge.svg)](https://github.com/danikiev/PyNetDesign/actions/workflows/pytest.yml)
[![Docs](https://github.com/danikiev/PyNetDesign/actions/workflows/docs.yml/badge.svg)](https://github.com/danikiev/PyNetDesign/actions/workflows/docs.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellowgreen.svg)](https://github.com/danikiev/PyNetDesign/blob/main/LICENSE)

PyNetDesign is an open-source Python framework for testing and designing microseismic monitoring networks for homogeneous velocity models.

PyNetDesign can determine the magnitude sensitivity of the microseismic monitoring network, i.e. estimate the minimum moment magnitude detectable using the given network or receivers.
It can work with both station networks and distributed acoustic sensing (DAS) cable networks at the same time.
Magnitude sensitivity is represented in the form of horizontal or vertical slices through a 3D grid.

## Installation

### Requirements

To clone the git repository use [Git](https://git-scm.com/), a free and open source distributed version control system.

Installation requires [Conda](https://conda.io) package manager, e.g. one can use [miniforge](https://github.com/conda-forge/miniforge) implementation.

PyNetDesign works with 3.9 <= `python` <= 3.12 and requires [`pip`](https://pypi.org/project/pip/).

The runtime dependencies are declared in `pyproject.toml`:

- [`numpy`](https://www.numpy.org/)
- [`pandas`](https://pandas.pydata.org/)
- [`matplotlib`](https://matplotlib.org/)
- [`cmcrameri`](https://pypi.org/project/cmcrameri/)

Two optional groups are available: `dev` adds `pytest` and a Jupyter stack, and `docs` adds the Sphinx toolchain.

The author is incredibly grateful to the developers of these and other packages used by PyNetDesign.

### Clone

First clone the git repository using

```sh
git clone https://github.com/danikiev/PyNetDesign.git
```

### Install

`environment.yml` pins only the interpreter, so create the environment and give it a name:

```bash
conda env create -f environment.yml -n pnd
```

**Note:** to speed up creation of the environment, use `mamba` instead of `conda`, which is a faster alternative.

Then activate the newly created environment:

```bash
conda activate pnd
```

Finally, install the package:

```bash
pip install -e .
```

### Installation using script

For quick installation, you can use the specially designed installation script which implement all of the above mentioned steps.

```bash
./install.sh            # Linux, macOS
install.bat             # Windows, from a Miniforge prompt
```

It creates the `pnd` environment and asks whether to add the development tools.
Pass `--dev` or `--no-dev` to `install.sh` to answer in advance.

### Installation for development

The development install adds the testing and documentation tools through the optional
dependency groups declared in `pyproject.toml`:

```bash
pip install -e ".[dev,docs]"
```

Or answer `y` when the installer asks whether to install the development tools:

```bash
./install.sh --dev      # Linux, macOS
install.bat             # Windows, then answer y
```

The `docs` group is what you need for building the [local documentation](#build-documentation-locally).

### Uninstall

If you need to add/change packages, deactivate the environment first:

```bash
conda deactivate
```

and then remove the appropriate environment:

```bash
conda remove -n pnd --all
```

You can also run the uninstallation script:

```bash
./uninstall.sh          # Linux, macOS
uninstall.bat           # Windows
```

It finds every Conda environment whose name starts with `pnd` and asks about each one.
Pass `--yes` to `uninstall.sh` to skip the questions.

## Documentation

The latest documentation, built with [Sphinx](https://www.sphinx-doc.org), is available at
<https://danikiev.github.io/PyNetDesign/>, and as a single downloadable PDF at
<https://danikiev.github.io/PyNetDesign/_static/pynetdesign.pdf>.

It features:

- Methodology
- Getting started guide
- Examples
- API reference

### Build documentation locally

The documentation tools are installed with the `docs` extra:

```bash
pip install -e ".[docs]"
```

Build it with the helper script, which does a clean build:

```bash
./build-docs.sh          # Linux, macOS
build-docs.bat           # Windows
```

Then view it in a browser. `serve-docs` rebuilds first, incrementally, so only the
pages that actually changed are regenerated:

```bash
./serve-docs.sh          # Linux, macOS
serve-docs.bat           # Windows
```

and open <http://localhost:8000>. Useful options:

| Option | Effect |
| --- | --- |
| `-p PORT`, `--port PORT` | serve on another port |
| `-n`, `--no-build` | serve what is already built, without rebuilding |
| `-i`, `--incremental` (`build-docs`) | skip the clean and rebuild only what changed |
| `--pdf` (`-pdf` on Windows) | also build the PDF, into `docs/build/html/_static` |

The PDF needs a LaTeX installation providing `lualatex` and `latexmk`; the scripts check
for both before starting and say so if either is missing.

Extra Sphinx options can be passed through `SPHINXOPTS`, for instance to build the
pages without running the examples:

```bash
SPHINXOPTS="-D plot_gallery=0" ./build-docs.sh    # Linux, macOS
set SPHINXOPTS=-D plot_gallery=0 && build-docs.bat  # Windows
```

Equivalently, without the scripts:

```bash
python -m sphinx -M html docs/source docs/build
```

and, for the PDF, generate the LaTeX sources and run `latexmk` on them:

```bash
python -m sphinx -M latex docs/source docs/build
cd docs/build/latex && latexmk -pdf -dvi- -ps- pynetdesign.tex
```

## Changelog

All notable changes are documented in [CHANGELOG.md](CHANGELOG.md), following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Citing

If you use PyNetDesign in your research, please cite it as follows:

**Anikiev, D. (2026).** *PyNetDesign: a Python framework for microseismic monitoring network design.* Zenodo.
<https://doi.org/10.5281/zenodo.22695001>

In BibTeX format:

```bibtex
@software{Anikiev2026PyNetDesign,
   author    = {Anikiev, Denis},
   title     = {{PyNetDesign}: a {P}ython framework for microseismic monitoring network design},
   year      = {2026},
   publisher = {Zenodo},
   doi       = {10.5281/zenodo.22695001},
   url       = {https://github.com/danikiev/PyNetDesign}
}
```

The DOI above represents all versions and will always resolve to the latest one.
To cite a particular version of PyNetDesign, please use the following format, e.g. for
version 1.0.1:

**Anikiev, D. (2026).** *PyNetDesign: a Python framework for microseismic monitoring network design (1.0.1).* Zenodo.
<https://doi.org/10.5281/zenodo.22695002>

In BibTeX format:

```bibtex
@software{Anikiev2026PyNetDesignVersion,
   author    = {Anikiev, Denis},
   title     = {{PyNetDesign}: a {P}ython framework for microseismic monitoring network design},
   year      = {2026},
   publisher = {Zenodo},
   version   = {1.0.1},
   license   = {MIT},
   doi       = {10.5281/zenodo.22695002},
   url       = {https://github.com/danikiev/PyNetDesign}
}
```

### Earlier release

Version 1.0.0 was deposited manually, before the automated GitHub–Zenodo integration was
enabled, and therefore belongs to a separate Zenodo lineage. It is cross-linked to the
current record and remains citable on its own:
<https://doi.org/10.5281/zenodo.14945917>

**Note:** magnitudes computed with version 1.0.0 are affected by an error in the seismic
moment calculation that was corrected in version 1.0.1. If you are citing or reusing
results obtained with 1.0.0, please see [CHANGELOG.md](CHANGELOG.md) and issue
[#3](https://github.com/danikiev/PyNetDesign/issues/3).

## License

PyNetDesign is released under the MIT License. See [LICENSE](LICENSE) for details.
