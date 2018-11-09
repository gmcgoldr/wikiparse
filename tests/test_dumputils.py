import bz2
import io

from wikiparse import dumputils


def test_cursor_generator():
    lines = [b"5:x:y\n", b"5:\n", b"\t \n", b"10:\n", b"11:\n"]
    lines = bz2.compress(b"".join(lines))
    lines = io.BytesIO(lines)
    reads = dumputils.cursor_generator(lines)
    assert list(reads) == [(0, 5), (5, 5), (10, 1), (11, -1)]


def test_multi_stream_generator(tmp_path):
    block1 = b"block1 content"
    block2 = b"block2 ..."
    block3 = b"block3"

    index = list()
    with (tmp_path / "file.bz2").open("wb") as fio:
        for block in block1, block2, block3:
            data = bz2.compress(block)
            index.append((fio.tell(), len(data)))
            fio.write(data)

    with (tmp_path / "file.bz2").open("rb") as fio:
        reader = dumputils.multi_stream_generator(fio, index, show_progress=False)
        assert list(reader) == [block1, block2, block3]

    with (tmp_path / "file.bz2").open("rb") as fio:
        reader = dumputils.multi_stream_generator(fio, index, show_progress=True)
        assert list(reader) == [block1, block2, block3]


def test_xml_generator():
    xml_data = (
        '<?xml version = "1.0"?>',
        "<outer-block>",
        "<sub-block-1>value\n1</sub-block-1>",
        "<sub-block-2>value2</sub-block-2>",
        "</outer-block>",
    )
    xml_bytes = (l.encode("utf8") for l in xml_data)

    xml_elements = dumputils.xml_generator(xml_bytes)

    tags, texts = zip(*[(e.tag, e.text) for e in xml_elements])
    assert tags == ("sub-block-1", "sub-block-2", "outer-block")
    assert texts == ("value\n1", "value2", None)
