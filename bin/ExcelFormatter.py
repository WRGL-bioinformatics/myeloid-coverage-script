import datetime
import sys
import xlsxwriter
from pathlib import Path
from bin.Config import config


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
            f"INFO: Creating coverage folder at {self.outputpath}", file=sys.stderr,
        )

        # Create an empty Excel workbook in the output folder
        self.workbook = xlsxwriter.Workbook(
            self.outputpath / f"{self.runid}_Coverage.xlsx"
        )

        # Write the summary/cover sheet
        self.write_summary()

        # Loop through each sample in the dict
        for sample in sorted(self.outputdict.keys()):
            sampleid = Path(sample).parts[-1].split("_")[0]
            self.write_sample(sample, sampleid)

        self.workbook.close()

    def write_summary(self):
        """
        Writes a cover sheet for the workbook, summarising some key metadata that
        can't be included on the individual sample pages
        """
        worksheet = self.workbook.add_worksheet("Summary")
        worksheet.write(
            1,
            1,
            "Myeloid panel coverage summary",
            self.workbook.add_format({"bold": True, "font_size": 14}),
        )
        worksheet.write(3, 1, self.runid, self.workbook.add_format({"bold": True}))
        worksheet.write(
            5, 1, "Samples", self.workbook.add_format({"bold": True, "border": 1})
        )
        for index, sample in enumerate(sorted(self.outputdict.keys())):
            worksheet.write(
                index + 6,
                1,
                Path(sample).parts[-1].split("_")[0],
                self.workbook.add_format({"border": 1}),
            )

        worksheet.write(
            5, 3, "Minimum depth", self.workbook.add_format({"bold": True, "border": 1})
        )
        worksheet.write(
            6,
            3,
            f"{config.get('coverage', 'mindepth')}x",
            self.workbook.add_format({"bold": True, "color": "red", "border": 1}),
        )

        # move the support footer line to just below the sample list, regardless of
        # how many samples are used
        worksheet.write(
            len(self.outputdict.keys()) + 10,
            1,
            f"WRGL software {datetime.datetime.now().year}.  Contact {config.get('general', 'admin_email')} for support",
            self.workbook.add_format({"color": "gray"}),
        )

        # Adjust column widths to fit the data nicely
        worksheet.set_column(1, 1, 20)
        worksheet.set_column(2, 2, 10)
        worksheet.set_column(3, 3, 20)
        worksheet.set_row(1, 30)

    def write_sample(self, sample: str, sampleid: str):
        """
        Uses XlsxWriter to make an Excel workbook containing the coverage summaries for
        every sample. Workbook name is taken from the run ID, and it is saved in the new
        data folder in a "Coverage" folder.
        """
        worksheet = self.workbook.add_worksheet(sampleid)
        print(f"INFO: Writing Excel report for {sampleid}", file=sys.stderr)

        # format object used to set panel headers to bold text
        header_format = self.workbook.add_format(
            {"bold": True, "text_wrap": True, "border": 1}
        )
        gene_format = self.workbook.add_format({"italic": True, "border": 1})
        gene_bold_format = self.workbook.add_format(
            {"italic": True, "bold": True, "border": 1}
        )
        other_format = self.workbook.add_format({"border": 1, "num_format": "0.00%"})

        # Add each panel starting at the position defined in the transfer.config file.
        for panel in config["panels"].getlist("panels"):

            # Create an offset so that we can start genes from the cell below thier
            # header. Include a check for headers not on row 1, as these are merged
            # double height cells (no, I don't know why...)
            columnoffset = 1
            rowoffset = 0
            if config.getint(panel, "row") != 0:
                rowoffset = 1

            worksheet.merge_range(
                config.getint(panel, "row"),
                config.getint(panel, "column"),
                config.getint(panel, "row") + rowoffset,
                config.getint(panel, "column") + columnoffset,
                panel,
                header_format,
            )

            # now write the actual data, for each panel as defined in transfer.config
            for index, gene in enumerate(config[panel].getlist("genes")):
                # Calculate the percentage coverage for the current gene
                length = self.outputdict[sample][gene][0]
                covered = self.outputdict[sample][gene][1]
                coverage = covered / length

                # Some genes should be highlighted in bold
                # Check the list from transfer.config and change the format as appropriate
                if gene in config["formatting"].getlist("bold"):
                    gene_fmt = gene_bold_format
                else:
                    gene_fmt = gene_format

                # Write the gene name and its coverage in the adjacent cell
                # rowoffset is used to account for double-row panel headers
                # NOTE: gene_fmt rather than gene_format below to allow bold to be set
                #       above.
                worksheet.write(
                    config.getint(panel, "row") + (index + 1 + rowoffset),
                    config.getint(panel, "column"),
                    gene,
                    gene_fmt,
                )
                worksheet.write(
                    config.getint(panel, "row") + (index + 1 + rowoffset),
                    config.getint(panel, "column") + 1,
                    coverage,
                    other_format,
                )

        # Adjust column widths to fit the data nicely
        worksheet.set_column(0, 7, 10)
        worksheet.set_column(10, 10, 25)
        worksheet.set_column(11, 11, 10)
        worksheet.set_row(0, 30)
