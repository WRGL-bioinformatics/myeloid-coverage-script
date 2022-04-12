"""
OpenGzip
=========

Author: Ben.Sanders@NHS.net

Returns an opened file handle, but allows for either gzipped
or uncompressed files to be opened neatly.

"""

# Disable the "Consider using 'with'" warning as it's inappropriate here
# pylint: disable=R1732

import gzip
import os
import shutil
import sys
from typing import TextIO
from pathlib import Path

def open_gzip(fname: str) -> TextIO:
    """
    Open gzip or uncompressed file and return open filehandle
    """
    try:
        # we have to open the file twice - once to check
        # it is a gzipped file
        with open(fname, 'rb') as fhandle:
            assert fhandle.read(2) == b'\x1f\x8b'
        # And again with gzip to read it as a text file.
        fhandle =  gzip.open(fname, "rt", encoding="utf-8")
    except AssertionError:
        # An assertion error means the file is NOT gzipped
        # and can be opened as a normal file.
        fhandle = open(fname, "r", encoding="utf-8")
    # Return the correctly opened file handle
    return fhandle

def decompress_gzip(fname: str, delete_original: bool=False) -> None:
    """
    Decompresses a gzipped file

    Gets filename from the input automatically

    DEV: Do we want to delete the original?
    """

    fpath = Path(fname)
    directory = fpath.parent
    # Path.stem removes the *last* extension, e.g. .gz?
    newfname = fpath.stem
    newfpath = directory / newfname
    # Double-check the new type - if it's not VCF, it wasn't compressed
    # so we don't need to do anything
    print(f"INFO: Decompressing {newfpath}")
    try:
        assert ".vcf" in newfname
    except AssertionError:
        print("INFO: File {fpath} is not gzipped, not extracting",
              file=sys.stderr)
        return None
    with open_gzip(fpath) as infile:
        with open(newfpath, "w", encoding="utf-8") as outfile:
            shutil.copyfileobj(infile, outfile)

    if delete_original:
        # Delete the original file, and it's index (if present)
        os.remove(fpath)
        os.remove(f"{fpath}.tbi")

    # pylint doesn't like an implicit None return here as we have an explicit
    # one earlier. Not sure why, but we'll add this to keep it happy.
    return None
