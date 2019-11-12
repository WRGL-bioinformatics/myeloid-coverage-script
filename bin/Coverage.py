"""
Author: Ben.Sanders@NHS.net

Calculate coverage for a myeloid panel run
"""

import sys
from pathlib import Path

# config is shared across multiple classes, so we load it up in its own module
# to avoid repetition of the config parsing code
from bin.Config import config
from bin.BedReader import BedReader
from bin.ExcelFormatter import ExcelFormatter


class MyeloidCoverage(object):
    """
    Handle generating coverage for an entire run folder
    """

    def __init__(self, runfolder: str):
        self.runfolder = Path(runfolder)
        print(
            "INFO: Gathering coverage files for run {}".format(
                self.runfolder.parts[-1]
            ),
            file=sys.stderr,
        )

        # Glob all genome VCFs in the run folder - these contain the
        # coverage information
        coveragefiles = list(self.runfolder.glob("*.genome.vcf"))

        assert len(coveragefiles) > 0, "ERROR: No genome vcf files detected"

        # Load the BED file target regions
        # DEV: It might be a good idea to edit the BedReader class to check that
        #      it has a Path, and to convert to one if passed a Str.
        self.bedfile = BedReader(Path(config.get("coverage", "bedfile")))
        self.bedregions = self.bedfile.bedfile

        # Analyse the coverage for each genome vcf file
        # Use the filename as key in the output dictionary
        outputdict = {}
        for f in coveragefiles:
            outputdict[f] = SampleCoverage(f, self.bedregions).coverage

        # Use ExcelFormatter to write the results into a correclty formatted Excel
        # workbook
        ExcelFormatter(outputdict)


class SampleCoverage(object):
    """
    Generate a coverage report for a single file
    """

    def __init__(self, vcf: str, bedfile: list):
        self.vcfpath = Path(vcf)
        # Extract just the sample ID from the genome VCF path
        self.sampleid = self.vcfpath.parts[-1].split("_")[0]
        print(
            "INFO: Reading coverage file for {}".format(self.sampleid), file=sys.stderr
        )
        # Make sure the file can be opened
        assert self.vcfpath.is_file(), "ERROR: File {} cannot be opened"
        self.bedregions = bedfile
        self.coveragedict = self.read_vcf(self.vcfpath)
        self.genedict = self.intersect_bed()

    @property
    def coverage(self) -> dict:
        return self.genedict

    def read_vcf(self, vcf: str) -> dict:
        """
        Extract the postiion and coverage information from a genome VCF
        """
        coveragedict = {}
        CHROM = None

        with vcf.open() as f:
            for line in f:
                line = line.rstrip().split()

                # Skip header lines
                if line[0].startswith("#"):
                    continue

                # Check if the chromosome has changed
                if str(CHROM) != line[0]:
                    try:
                        CHROM = int(line[0])
                    except ValueError:

                        # This will store non-numeric chromosomes (e.g. X & Y) as
                        # strings, while storing the others are ints
                        CHROM = line[0]
                    print(
                        "INFO: Reading chromosome {} coverage".format(CHROM),
                        file=sys.stderr,
                    )

                # POS is the second line of the file
                POS = int(line[1])

                # In a genome VCF there is a DP= field in the INFO column with the depth
                # We just have to make sure that this can cope with multiple INFO fields
                INFO = line[7].split(";")
                for field in INFO:
                    if field.startswith("DP="):
                        DEPTH = int(field.split("=")[1])

                # Skip adding if depth is zero
                if DEPTH == 0:
                    continue

                # Add to the coverage dictionary
                # try/excepts cover the possibilities of sample not added and
                # chromosome not added. Then POS and DEPTH can be.
                try:
                    coveragedict[CHROM][POS] = DEPTH
                except KeyError:
                    try:
                        coveragedict[CHROM] = {POS: DEPTH}
                    except KeyError:
                        coveragedict = {CHROM: {POS: DEPTH}}
        return coveragedict

    def intersect_bed(self) -> dict:
        """
        Use the bed ROI list to extract only the parts of the coverage dict that:

        1) Are within the ROI
        2) Are above the minimum required coverage

        and return as a new dictionary which summarises this per gene, rather than per
        exon/amplicon   
        """
        print(
            "INFO: Analysing coverage for sample {}".format(self.sampleid),
            file=sys.stderr,
        )

        # Use a new dictionary, which will store coverage details per-gene
        genedict = {}

        # The required minimum depth of coverage is adjustable from the config file
        mindepth = config.getint("coverage", "mindepth")

        # Process each ROI in turn (could possibly do in parallel but it's quick enough)
        for roi in self.bedregions:
            CHR = roi[0]
            START = roi[1]
            END = roi[2]
            NAME = roi[3]

            # If the gene is already in the dictionary, we want to update the length
            # If not, we want to add it.
            # NOTE: The dict value is a list of length and coverage, and I haven't
            #       Figured out a way to create and update a new list with dict.get()
            try:
                genedict[NAME][0] = genedict[NAME][0] + (END - START)
            except KeyError:
                genedict[NAME] = [(END - START), 0]

            # BED format is 0-indexed while coverage file is 1-indexed. So we have to
            # add 1 to the start and end
            for POS in range(START + 1, END + 1):
                try:
                    if self.coveragedict[CHR][POS] >= mindepth:
                        genedict[NAME][1] += 1
                    genedict[NAME][1] = genedict[NAME][1]
                except KeyError:
                    # If nothing found, assume the depth is 0
                    # print("WARNING: Position not found", file=sys.stderr)
                    genedict[NAME][1] = genedict[NAME][1]
        return genedict

    def write_coverage(self):
        """
        Write a per-sample text file output of the results

        DEPRECATED - use ExcelFormatter output instead
        """
        self.outputpath = self.vcfpath.parent / "Coverage"
        self.outputpath.mkdir(exist_ok=True, parents=True)
        outfile = self.outputpath / "{}_Coverage.txt".format(self.sampleid)
        with outfile.open("w") as f:

            # Write a header for the coverage file
            f.write("## Coverage report for sample {}\n".format(self.sampleid))
            f.write(
                "## Minimum depth required: {}x\n".format(
                    config.getint("coverage", "mindepth")
                )
            )
            f.write("#GENE\tLENGTH\tCOVERED\tPERCENTAGE\n")

            # Now write the coverage summary for each gene
            for gene in self.genedict.keys():
                length = self.genedict[gene][0]
                coverage = self.genedict[gene][1]
                percentage = (coverage / length) * 100
                assert (
                    length >= coverage
                ), "ERROR: {} has more coverage than length".format(gene)
                f.write(
                    "{}\t{}\t{}\t{:.2f}\n".format(gene, length, coverage, percentage)
                )
