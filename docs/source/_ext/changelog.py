from __future__ import annotations

from pathlib import Path
import re


_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
# A markdown code span closes with as many backticks as it opened with, so both `x`
# and ``x`` become an rst literal
_INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
# Keep a Changelog writes a version heading as a link reference, "## [v1.1.0] - date",
# that a "[v1.1.0]: url" definition at the end of the file resolves
_LINK_DEFINITION_RE = re.compile(r"^\[([^\]]+)\]:\s*(\S+)\s*$")
_LINKED_TITLE_RE = re.compile(r"^\[([^\]]+)\](?!\()(.*)$")
_COMPARE_URL_RE = re.compile(r"/compare/(.+?)\.\.\.")
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
    text = _INLINE_CODE_RE.sub(r"``\2``", text)
    return _LINK_RE.sub(r"`\1 <\2>`_", text)


def _version_link(url: str) -> str:
    """Word the link under a version heading after the page it opens."""
    where = " on GitHub" if "github.com" in url else ""
    compare = _COMPARE_URL_RE.search(url)
    text = f"Compare with {compare.group(1)}" if compare else "Release"
    return f"`{text}{where} <{url}>`__"


def _convert_heading(line: str, links: dict[str, str]) -> list[str] | None:
    match = re.match(r"^(#{2,3})\s+(.*)$", line)
    if not match:
        return None

    level = len(match.group(1))
    title = match.group(2).strip()
    url = None
    linked = _LINKED_TITLE_RE.match(title)
    if linked:
        title = linked.group(1) + linked.group(2)
        url = links.get(linked.group(1).lower())
    title = _convert_inline_markdown(title)
    marker = _HEADING_MARKERS.get(level, "-")
    block = ["", title, marker * len(title), ""]
    if url:
        block += [_version_link(url), ""]
    return block


def markdown_changelog_to_rst(markdown_text: str) -> str:
    output: list[str] = []
    in_releases = False
    # The link definitions are placed under their version headings instead of being
    # printed at the end; markdown matches link labels case-insensitively
    links = {
        definition.group(1).lower(): definition.group(2)
        for definition in map(_LINK_DEFINITION_RE.match, markdown_text.splitlines())
        if definition
    }

    for line in markdown_text.splitlines():
        if not in_releases:
            if re.match(r"^##\s+", line):
                in_releases = True
            else:
                continue

        if line.startswith("# ") or _LINK_DEFINITION_RE.match(line):
            continue

        heading_block = _convert_heading(line, links)
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
