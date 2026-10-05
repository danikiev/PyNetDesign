"""Send every citation to a bibliography that the current build writes.

The HTML pages list their own references at the bottom, inside ``.. only:: html``,
while the PDF collects all of them in a single ``.. only:: latex`` bibliography, which
Sphinx moves to the end of the document. sphinxcontrib-bibtex resolves each citation to
one bibliography holding its key, chosen without regard to the builder, so the PDF
linked to lists that only the HTML has, and the HTML could link to the list that only
the PDF has. Once sphinxcontrib-bibtex has collected the citations, this extension drops
those of the bibliographies that the current builder leaves out, so that every citation
resolves to a bibliography that is actually written.
"""

from sphinx import addnodes
from sphinxcontrib.bibtex.nodes import bibliography


def _is_written(node, tags):
    """Whether no enclosing ``only`` directive excludes the node from this build."""
    while node is not None:
        if isinstance(node, addnodes.only) and not tags.eval_condition(node["expr"]):
            return False
        node = node.parent
    return True


def _drop_unwritten_citations(app, env):
    domain = env.get_domain("cite")
    unwritten = set()
    for docname in {key.docname for key in domain.bibliographies}:
        for node in env.get_doctree(docname).findall(bibliography):
            if not _is_written(node, app.builder.tags):
                unwritten.add((docname, node["ids"][0]))
    domain.citations[:] = [
        citation
        for citation in domain.citations
        if (citation.bibliography_key.docname, citation.bibliography_key.id_)
        not in unwritten
    ]
    return []


def setup(app):
    # sphinxcontrib-bibtex collects the citations on env-updated at the default priority
    app.connect("env-updated", _drop_unwritten_citations, priority=900)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
