import sys
import xlsxwriter
from pathlib import Path
from ExcelGenes import genedict
from ExcelGenes import boldgenes


class ExcelFormatter(object):
    """
    Uses the formatting options defined in ExcelGenes.py to write an Excel workbook that
    matches the current formatting of the Excel report exactly (following the scripts
    that Richard made in cooperation with the Myeloid team.) Reports 100x minimum
    coverage level, but this is adjustable via the config file.
    """

    def __init__(self, outputdict: dict):

        # Get the output path from the first vcf path in the output
        # Create a Path object and point it to the Coverage folder
        self.outputdict = outputdict
        self.outputpath = Path(next(iter(self.outputdict))).parent / "Coverage"
        self.outputpath.mkdir(exist_ok=True, parents=True)
        self.runid = self.outputpath.parts[-2]
        print(
            "INFO: Creating coverage folder at {}".format(self.outputpath),
            file=sys.stderr,
        )

        # Create an empty Excel workbook in the output folder
        self.workbook = xlsxwriter.Workbook(
            self.outputpath / "{}_Coverage.xlsx".format(self.runid)
        )

        # Loop through each sample in the dict
        for sample in self.outputdict.keys():
            sampleid = Path(sample).parts[-1].split("_")[0]
            self.write_sample(sample, sampleid)

        self.workbook.close()

    def write_sample(self, sample: str, sampleid: str):
        """
        Uses XlsxWriter to make an Excel workbook containing the coverage summaries for
        every sample. Workbook name is taken from the run ID, and it is saved in the new
        data folder in a "Coverage" folder.
        """
        worksheet = self.workbook.add_worksheet(sampleid)
        print("INFO: Writing Excel report for {}".format(sampleid), file=sys.stderr)

        # format object used to set panel headers to bold text
        header_format = self.workbook.add_format(
            {"bold": True, "text_wrap": True, "border": 1}
        )
        gene_format = self.workbook.add_format({"italic": True, "border": 1})
        gene_bold_format = self.workbook.add_format(
            {"italic": True, "bold": True, "border": 1}
        )
        other_format = self.workbook.add_format({"border": 1})

        # Add each panel starting at the position defined in the ExcelGenes.py dictionary.
        for panel in genedict.keys():

            # Create an offset so that we can start genes from the cell below thier
            # header. Include a check for headers not on row 1, as these are merged
            # double height cells (no, I don't know why...)
            columnoffset = 1
            rowoffset = 0
            if genedict[panel]["row"] != 0:
                rowoffset = 1

            worksheet.merge_range(
                genedict[panel]["row"],
                genedict[panel]["column"],
                genedict[panel]["row"] + rowoffset,
                genedict[panel]["column"] + columnoffset,
                panel,
                header_format,
            )

            # now right the actual data
            for index, gene in enumerate(genedict[panel]["genes"]):
                # Calculate the percentage coverage for the current gene
                length = self.outputdict[sample][gene][0]
                covered = self.outputdict[sample][gene][1]
                coverage = "{:.2f}%".format((covered / length) * 100)

                # Some genes should be highlighted in bold
                # Check the list from ExcelGenes.py and change the format as appropriate
                if gene in boldgenes:
                    gene_fmt = gene_bold_format
                else:
                    gene_fmt = gene_format

                # Write the gene name and its coverage in the adjacent cell
                # rowoffset is used to account for double-row panel headers
                # NOTE: gene_fmt rather than gene_format below to allow bold to be set
                #       above.
                worksheet.write(
                    genedict[panel]["row"] + (index + 1 + rowoffset),
                    genedict[panel]["column"],
                    gene,
                    gene_fmt,
                )
                worksheet.write(
                    genedict[panel]["row"] + (index + 1 + rowoffset),
                    genedict[panel]["column"] + 1,
                    coverage,
                    other_format,
                )

        # Adjust column widths to fit the data nicely
        worksheet.set_column(0, 7, 10)
        worksheet.set_column(10, 10, 25)
        worksheet.set_column(11, 11, 10)
        worksheet.set_row(0, 30)
