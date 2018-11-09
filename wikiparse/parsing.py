"""
Functionality for parsing wikipedia pages.

Loosely based around
https://github.com/RaRe-Technologies/gensim/blob/develop/gensim/corpora/wikicorpus.py
"""

import html
import re
import unicodedata
import xml.etree.cElementTree as ET
from typing import Iterable, Tuple

import mwparserfromhell as mw

IGNORED_SEQUENCES = {"References", "External links", "See also"}


def _parse_namespace(element):
    match = re.match(r"{[^}]+}", element.tag)
    namespace = match.group()[1:-1] if match else ""
    if not namespace.startswith("http://www.mediawiki.org/xml/export-"):
        raise RuntimeError(f"{namespace} not recognized as MediaWiki namespace")
    return namespace


def page_generator(
    xml: Iterable[ET.Element]
) -> Iterable[Tuple[str, mw.wikicode.Wikicode]]:
    namespace = _parse_namespace(next(xml))

    page_tag = f"{{{namespace}}}page"
    text_path = f"./{{{namespace}}}revision/{{{namespace}}}text"
    title_path = f"./{{{namespace}}}title"
    ns_path = f"./{{{namespace}}}ns"

    # fix HTML tags whose tag name is immediately followed by a new line. This
    # appears to be a bug in mwparserfromhell.
    re_html_nl = re.compile(r"(<[a-zA-Z]+)\n([^>]*>)")

    # keep a stack of ET.Element objects that can be cleared to avoid
    # accumulating the entire wikipedia XML in memory
    to_clear = list()

    for element in xml:
        to_clear.append(element)

        if not (element.tag == page_tag and element.find(ns_path).text == "0"):
            continue

        title = element.find(title_path).text
        markup = element.find(text_path).text
        markup = re_html_nl.sub(r"\1 \2", markup)
        doc = mw.parse(markup)

        yield title, doc

        # this point is reached after parsing a page, can clear since it won't
        # affect the next page
        list(map(lambda e: e.clear(), to_clear))
        to_clear = list()


def _normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)

    text = text.replace("\u2012", "-")
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")

    text = text.replace("\u2018", "'")
    text = text.replace("\u2019", "'")
    text = text.replace("\u201C", '"')
    text = text.replace("\u201D", '"')

    return text


def nlp_generator(pages: Iterable[Tuple[str, mw.wikicode.Wikicode]]):
    for title, doc in pages:
        # remove tabular nodes from mediawiki tree
        tables = [
            node
            for node in doc.nodes
            if isinstance(node, mw.nodes.tag.Tag)
            and (node.tag == "table" or node.tag == "ref")
        ]
        # don't remove during iteration
        for table in tables:
            doc.remove(table)

        # strip wikimedia code
        text = doc.strip_code(normalize=True, collapse=True)
        # strip HTML
        text = html.unescape(text)
        # normalize ascii
        text = _normalize_text(text)
        # common problems after stripping
        text = text.replace("()", "")
        text = text.replace("[]", "")
        text = text.replace("<>", "")
        text = text.replace("(; ", "(")
        text = text.replace("\\'", "'")
        text = text.replace("'''", "")
        text = text.replace("''", '"')

        # ignore re-direct pages
        if text.startswith("REDIRECT"):
            continue

        paragraphs = [paragraph.strip() for paragraph in text.split("\n")]

        # filter commonly problematic paragraphs
        paragraphs = [
            paragraph
            for paragraph in paragraphs
            if paragraph
            # should start with an upper case letter
            and paragraph[0].isalpha() and paragraph[0].isupper()
            # ignore category meta-data
            and not paragraph.startswith("Category:")
            # some common mediawiki headers without meaning
            and not paragraph in IGNORED_SEQUENCES
        ]

        if not paragraphs:
            continue

        yield title, paragraphs
