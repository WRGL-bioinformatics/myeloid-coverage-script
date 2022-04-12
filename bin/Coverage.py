"""
Author: Ben.Sanders@NHS.net

Calculate coverage for a myeloid panel run
"""

import sys
from pathlib import Path

# config is shared across multiple classes, so we load it up in its own module
# to avoid repetition of the config parsing code
from bin.Config import config
from bin.bed_reader import BedReader
from bin.excel_formatter import ExcelFormatter
from bin.open_gzip import open_gzip, decompress_gzip

class MyeloidCoverage():
    """
    Handle generating coverage for an entire run folder
    """

    def __init__(self, runfolder: str):
        self.runfolder = Path(runfolder)
        
        print(
            f"INFO: Gathering coverage files for run {self.runfolder.parts[-2]}",
            file=sys.stderr,
        )

        # Glob all genome VCFs in the run folder - these contain the
        # coverage information
        # DEV: This will need to allow for LRM gzipped genome vcfs.
        #      Should be ok to use "*.genome.vcf*" to capture both
        coveragefiles = list(self.runfolder.glob("*.genome.vcf"))
        try:
            assert len(coveragefiles) > 0, "ERROR: No genome vcf files detected"
        except AssertionError:
            # If there are gzipped VCFs, unzip *all* of them, not just
            # genome VCFs.
            coveragefiles = list(self.runfolder.glob("*.vcf.gz"))
            for covfile in coveragefiles:
                # Decompress to a .vcf file
                decompress_gzip(covfile, delete_original=True)

            # regenerate the coveragefiles
            coveragefiles = list(self.runfolder.glob("*.genome.vcf"))

        # Load the BED file target regions
        # BED file has the full path in transfer.config, so it doesn't need to
        # be resolved relative to the script/executable
        self.bedfile = BedReader(Path(config.get("coverage", "bedfile")))
        self.bedregions = self.bedfile.bedfile

        # Analyse the coverage for each genome vcf file
        # Use the filename as key in the output dictionary
        outputdict = {}
        for covfile in coveragefiles:
            outputdict[covfile] = SampleCoverage(
                                                 covfile, self.bedregions
                                                ).coverage

        # Use ExcelFormatter to write the results into a correclty formatted
        # Excel workbook
        ExcelFormatter(outputdict)

    @property
    def get_runfolder(self):
        """This is just to try and clear a 'too few public methods' message"""
        return self.runfolder

    @property
    def placeholder(self):
        """Another 'too few public methods' function..."""
        return None


class SampleCoverage():
    """
    Generate a coverage report for a single file

    DEV: Update this to handle both gzipped and uncompressed vcfs
    """

    def __init__(self, vcf: str, bedfile: list):
        self.vcfpath = Path(vcf)
        self.outputpath = self.vcfpath.parent / "Coverage"
        # Extract just the sample ID from the genome VCF path
        self.sampleid = self.vcfpath.parts[-1].split("_")[0]
        print(f"INFO: Reading coverage file for {self.sampleid}",
              file=sys.stderr)
        # Make sure the file can be opened
        assert self.vcfpath.is_file(), "ERROR: File {} cannot be opened"
        self.bedregions = bedfile
        self.coveragedict = self.read_vcf(self.vcfpath)
        self.genedict = self.intersect_bed()

    @property
    def coverage(self) -> dict:
        """
        Return the coverage dictionary
        """
        return self.genedict

    @staticmethod
    def read_vcf(vcf: Path) -> dict:
        """
        Extract the postiion and coverage information from a genome VCF

        DEV: open gzipped vcf too! Might need to be handled as a function - so
        we can try opening compressed or uncompressed and just return the file
        handle. Does that still then work with the "with" construct?
        """
        coveragedict = {}
        chrom = None

        with open_gzip(vcf) as fhandle:
            for line in fhandle:
                line = line.rstrip().split()

                # Skip header lines
                if line[0].startswith("#"):
                    continue

                # Check if the chromosome has changed
                if str(chrom) != line[0]:
                    try:
                        chrom = int(line[0])
                    except ValueError:

                        # This will store non-numeric chromosomes (e.g. X & Y)
                        # as strings, while storing the others are ints
                        chrom = line[0]
                    print(
                        f"INFO: Reading chromosome {chrom} coverage",
                        file=sys.stderr,
                    )

                # POS is the second line of the file
                pos = int(line[1])

                # In a genome VCF there is a DP= field in the INFO column with
                # the depth. We just have to make sure that this can cope with
                # multiple INFO fields
                info = line[7].split(";")
                for field in info:
                    if field.startswith("DP="):
                        depth = int(field.split("=")[1])

                # Skip adding if depth is zero
                if depth == 0:
                    continue

                # Add to the coverage dictionary
                # try/excepts cover the possibilities of sample not added and
                # chromosome not added. Then POS and DEPTH can be.
                try:
                    coveragedict[chrom][pos] = depth
                except KeyError:
                    try:
                        coveragedict[chrom] = {pos: depth}
                    except KeyError:
                        coveragedict = {chrom: {pos: depth}}
        return coveragedict

    def intersect_bed(self) -> dict:
        """
        Use bed ROI list to extract only the parts of the coverage dict that:

        1) Are within the ROI
        2) Are above the minimum required coverage

        and return as a new dictionary which summarises this per gene, rather
        than per exon/amplicon
        """
        print(
            f"INFO: Analysing coverage for sample {self.sampleid}",
            file=sys.stderr,
        )

        # Use a new dictionary, which will store coverage details per-gene
        genedict = {}

        # The required minimum depth of coverage is set from the config file
        mindepth = config.getint("coverage", "mindepth")

        # Process each ROI in turn (could do in parallel but it's quick enough)
        for roi in self.bedregions:
            chrom = roi[0]
            start = roi[1]
            end = roi[2]
            name = roi[3]

            # If the gene is already in the dictionary, we want to update the
            # length If not, we want to add it.
            # NOTE: The dict value is a list of length and coverage, and I
            #       haven't Figured out a way to create and update a new list
            #       with dict.get()
            try:
                genedict[name][0] = genedict[name][0] + (end - start)
            except KeyError:
                genedict[name] = [(end - start), 0]

            # BED format is 0-indexed while coverage file is 1-indexed. So we
            # have to add 1 to the start and end
            for pos in range(start + 1, end + 1):
                try:
                    if self.coveragedict[chrom][pos] >= mindepth:
                        genedict[name][1] += 1
                    genedict[name][1] = genedict[name][1]
                except KeyError:
                    # If nothing found, assume the depth is 0
                    # print("WARNING: Position not found", file=sys.stderr)
                    genedict[name][1] = genedict[name][1]
        return genedict
