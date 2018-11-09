"""
Iterate over wikipedia multi-stream bz2 and XML.
"""

import bz2
import logging
import xml.etree.cElementTree as ET
from typing import BinaryIO, Iterable, Tuple

from tqdm import tqdm


def cursor_generator(index_lines: Iterable[bytes]) -> Iterable[Tuple[int, int]]:
    """
    Generate cursor position and read size for each compressed block. Parses
    the contents of the `*-multistream-index.txt.bz2` file.

    Arguments:
        index_lines: iterator over lines of the index file

    Returns:
        cursor position and block size
    """
    last_cursor = 0

    for line in index_lines:
        line = line.decode("utf8")
        if not line.strip():
            continue

        # TODO: catch and return module error
        cursor = int(line.split(":")[0])

        if cursor == last_cursor:
            continue

        yield last_cursor, cursor - last_cursor
        last_cursor = cursor

    yield last_cursor, -1


def multi_stream_generator(
    fio: BinaryIO, index: Iterable[Tuple[int, int]], show_progress: bool = True
) -> Iterable[bytes]:
    """
    Generate blocks of decompressed data.

    Arguments:
        fio: io of compressed data indexed with `index`
        index: tuples of cursor position and read size in `fio`
        show_progress: (optional) if true, wrap reading loop in tqdm progress
            bar. Note that this requires pre-computing the index.

    Returns:
        blocks of decompressed data
    """
    if show_progress:
        # to show progress, need to pre-compute the index
        logging.info("parsing index...")
        iterable = tqdm(list(index))
    else:
        iterable = index

    # iterate over compressed blocks to read
    for cursor, size in iterable:
        fio.seek(cursor)
        data = fio.read(size)

        try:
            data = bz2.decompress(data)
        except OSError:
            logging.warning("bz2 error at cursor %s", cursor)
            continue

        yield data


def xml_generator(data: Iterable[bytes]) -> Iterable[ET.Element]:
    """
    Generate XML elements from a stream of utf-8 encoded XML bytes.

    Arguments:
        data: chunks of XML data with complete tags

    Returns:
        XML elements
    """
    parser = ET.XMLPullParser()
    ichunk = -1

    for chunk in data:
        ichunk += 1

        try:
            chunk = chunk.decode("utf8")
            parser.feed(chunk)
        except ET.ParseError:
            logging.warning("XML parsing error at chunk %s", ichunk)
            continue

        for _, element in parser.read_events():
            yield element
