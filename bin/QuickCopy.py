"""
QuickCopy
=========

Author: Ben.Sanders@NHS.net

Adds a check for shutil copy functions to avoid overwriting existing files.
This should help speed up transfers when (e.g.) fastq files have already been
copied by the pipeline, while still allowing for full manual running if needed.

"""

from pathlib import Path
import shutil


def quickcopy(src, dst, follow_symlinks=True):
    """
    Use the shutil copy function, but check whether the file already exists.
  
    Can be used in copytree as the copy_function to allow recursive copying
    with checking.

    NOTE: This does NOT check if src and dst are identical
    """
    # Just in case the full paths aren't given, work it out here
    # Using as a copy_function by shutil.copytree should provide full paths
    # Path is quite efficient, so there doesn't seem to be any real loss when
    # casting both these as paths
    fname = Path(src).name
    destpath = Path(dst).parent
    newfname = destpath / fname
    # test if the new file already exsists
    if newfname.exists():
        # Mimic the expected behaviour - return the path to the new file
        # Might need to be a string?
        return newfname
    return shutil.copy(src, dst, follow_symlinks=follow_symlinks)
