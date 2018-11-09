import os
import xml.etree.cElementTree as ET

import pytest

from wikiparse import parsing


@pytest.fixture
def xml_tree():
    path = os.path.realpath(__file__)
    path = os.path.dirname(path)
    path = os.path.join(path, "data", "sample.xml")
    tree = ET.parse(path)
    return tree


def test_page_generator(xml_tree):
    pages = parsing.page_generator(xml_tree.iter())

    title, doc = next(pages)
    assert title == "AccessibleComputing"
    assert (
        doc
        == "#REDIRECT [[Computer accessibility]]\n\n{{R from move}}\n{{R from CamelCase}}\n{{R unprintworthy}}"
    )

    title, doc = next(pages)
    assert title == "Anarchism"
    # test only the first node, long article
    assert (
        doc.nodes[0]
        == "{{redirect2|Anarchist|Anarchists|the fictional character|Anarchist (comics)|other uses|Anarchists (disambiguation)}}"
    )

    with pytest.raises(StopIteration):
        next(pages)


def test_nlp_generator(xml_tree):
    pages = parsing.page_generator(xml_tree.iter())
    nlp = parsing.nlp_generator(pages)

    title, strings = next(nlp)
    # note redirect is skipped
    assert title == "Anarchism"

    assert strings[0][:50] == "Anarchism is a political philosophy that advocates"
    assert strings[-1][:50] == 'Woodcock, George, ed., "The Anarchist Reader" (Fon'

    with pytest.raises(StopIteration):
        next(nlp)
