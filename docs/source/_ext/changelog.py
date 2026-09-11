from __future__ import annotations

from pathlib import Path
import re


_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_INLINE_CODE_RE = re.compile(r"`([^`]+)`")
_HEADING_MARKERS = {
    2: "^",
    3: '"',
}

_PAGE_HEADER = """.. _changelog:

=========
Changelog
=========

.. This page is generated from CHANGELOG.md by docs/source/_ext/changelog.py when the
   documentation is built, so that the changelog has a single source. Do not edit it by
   hand, and do not commit it: edit CHANGELOG.md instead.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.1.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

"""


def _convert_inline_markdown(text: str) -> str:
    text = _INLINE_CODE_RE.sub(r"``\1``", text)
    return _LINK_RE.sub(r"`\1 <\2>`_", text)


def _convert_heading(line: str) -> list[str] | None:
    match = re.match(r"^(#{2,3})\s+(.*)$", line)
    if not match:
        return None

    level = len(match.group(1))
    title = _convert_inline_markdown(match.group(2).strip())
    marker = _HEADING_MARKERS.get(level, "-")
    return ["", title, marker * len(title), ""]


def markdown_changelog_to_rst(markdown_text: str) -> str:
    output: list[str] = []
    in_releases = False

    for line in markdown_text.splitlines():
        if not in_releases:
            if re.match(r"^##\s+", line):
                in_releases = True
            else:
                continue

        if line.startswith("# "):
            continue

        heading_block = _convert_heading(line)
        if heading_block is not None:
            output.extend(heading_block)
            continue

        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]

        if stripped.startswith(("- ", "* ")):
            bullet = stripped[2:]
            output.append(f"{indent}- {_convert_inline_markdown(bullet)}")
            continue

        output.append(_convert_inline_markdown(line))

    return "\n".join(output).lstrip() + "\n"


def generate_changelog_page(project_root: Path, docs_source: Path) -> Path:
    """Render CHANGELOG.md into docs/source/changelog.rst.

    The whole page is generated, so it is listed in .gitignore and never committed.
    """
    changelog_md = project_root / "CHANGELOG.md"
    generated_file = docs_source / "changelog.rst"

    body = markdown_changelog_to_rst(changelog_md.read_text(encoding="utf-8"))
    generated_file.write_text(_PAGE_HEADER + body, encoding="utf-8")
    return generated_file
