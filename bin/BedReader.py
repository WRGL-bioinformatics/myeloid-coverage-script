"""
Author: Ben.Sanders@NHS.net

Read a BED file and store the regions of interest in a list.
"""

import sys
from pathlib import Path


class BedReader(object):
    """
    BED files are really quick and easy to read. This pulls each ROI out into a list of
    tuples representing (CHR, START, END, NAME). The positions of these fields are
    fixed by the BED specification, so should not vary.

    WRGL name format is used, where the gene name is stored in the first section of an
    underscore (_) delimited list. Additional information can be provided after the gene
    name (e.g. exon number), but the format of this is NOT fixed and may vary depending
    on who made the BED file, when it was made, etc. For this script, everything after
    the first underscore is discarded. Therefore, if you want to include additional
    information in the gene name (e.g. to report regions separately - see the hotspot
    regions in the Myeloid panel bed) the ROI names must be unique BEFORE the first
    underscore.
    e.g. JAK2_hotspotV617F_1 and JAK2_exon1 will be merged into JAK2, while
         JAK2hotspotV617F_1 and JAK2_exon1 will be reported separately.
    """

    def __init__(self, fpath):
        self.fpath = fpath
        self.fname = self.fpath.name
        print("INFO: Reading BED file {}".format(self.fname), file=sys.stderr)

        self._bedfile = self.read_bed_file()

    @property
    def bedfile(self) -> list:
        """Return the parse bed region list"""
        return self._bedfile

    @property
    def bedfilename(self) -> str:
        """Return the name of the target BED file (minus .bed extension)"""
        return self.fpath.stem

    def read_bed_file(self) -> list:
        """
        Open a BED file and read it into list (this is probably better than a dict since
        it retains the order)
        """
        bedfile = []
        try:
            with self.fpath.open() as f:
                for line in f:

                    # We only want the first 4 columns - CHROM, START, END, and NAME
                    # NAME is optional by BED spec, so if it's missing, generate an ID
                    # from the other fields
                    line = line.rstrip().split()

                    # Cast the numerical chromosomes to int, but leave X and Y as
                    # strings
                    try:
                        CHR = int(line[0])
                    except ValueError:
                        CHR = line[0]

                    # Start and end positions are integers
                    START = int(line[1])
                    END = int(line[2])
                    try:

                        # The gene name is, by WRGL convention, the first part of the ROI
                        # description, which is underscore delimited.
                        # If there is no NAME column, line[3] will raise an IndexError.
                        # In that case, just create an ID using the ROI coordinates.
                        NAME = line[3].split("_")[0]
                        line = (CHR, START, END, NAME)
                    except IndexError:
                        line = (CHR, START, END, "{}:{}-{}".format(CHR, START, END))

                    # Add to the BED file list
                    bedfile.append(line)

        # A BED file is required, so if it can't be opened quit.
        except FileNotFoundError:
            print(
                "ERROR: Could not open essential file {}".format(self.fname),
                file=sys.stderr,
            )
            sys.exit(1)

        return bedfile
