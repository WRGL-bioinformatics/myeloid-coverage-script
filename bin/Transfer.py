"""
Myeloid automatic file transfer
===============================

Author: ben.sanders@nhs.net

purpose
-------

Allow the user to select a run folder containing a myeloid
sequencing run, then a  target directory, then copy files from
the sequencing run to the backup directory.

"""

import sys
import tkinter as tk
from tkinter import filedialog
from pathlib import Path

from shutil import copytree

# config is shared across multiple classes, so we load it up in its own module
# to avoid repetition of the config parsing code
from bin.Config import config
from bin.quick_copy import quickcopy


class MyeloidTransfer():
    """
    Handles file copy operations to move Myeloid data to the network drive.
    """
    def __init__(self, datadir: str = None):
        # Get the run folder and target folder
        print(
            f"INFO: Default source directory: {config.get('directories', 'source-dir')}"
        )
        print(
            f"INFO: Default target directory: {config.get('directories', 'target-dir')}"
        )

        # Get the folder details from the user
        datadir, targetdir = self.get_details_tk(datadir)

        # Run the data transfer to the network
        self.newdatadir = self.transfer_files(datadir, targetdir)

    @property
    def newdatadirectory(self):
        """
        Return the new data directory target for copying

        This needs to be available for the coverage report generation step.
        """
        return self.newdatadir

    def transfer_files(self, datadir: Path, targetdir: Path) -> str:
        """
        Transfer the essential run files from the MiSeq run data folder to the
        backup target folder.
        """
        print(f"INFO: Selected run folder: {datadir}", file=sys.stderr)
        print(f"INFO: Selected destination folder: {targetdir}",
                                                        file=sys.stderr)

        # Extract the run ID from the data folder path
        # Since the MiSeq data directory structure is fixed, we know exactly
        # which section of the path has this, but we have to go from the end as
        # there could be changes before

        # DEV: There are some pretty major structure changes between MSR and LRM
        #      runs in the runid, basecallsdir and especially the rundir
        #      There will need to be a check to identify LRM runs and them do 

        if "Alignment_" in datadir.parts[-2]:
            print("INFO: Path suggests LRM-style run.")
            runid = datadir.parts[-3]
            # datadir is the alignment folder
            # For some of this we will need the BaseCalls folder above it
            basecallsdir = datadir / "Fastq"
            # And for some we will need the root run folder
            rundir = datadir.parent.parent
        else:
            print("INFO: Path suggests older MSR-style run.")
            runid = datadir.parts[-5]
            # datadir is the alignment folder
            # For some of this we will need the BaseCalls folder above it
            basecallsdir = datadir.parent
            # And for some we will need the root run folder
            rundir = datadir.parent.parent.parent.parent

        print(f"INFO: Folder run ID = {runid}", file=sys.stderr)

        # Create new folder in the target directory
        newrundir = targetdir / runid
        # this is the folder to hold the bams/vcfs
        newdatadir = newrundir / f"Myeloid_{config.get('general', 'version')}"
        # For Fastq backup
        newfastqdir = newrundir / "Data" / "Intensities" / "BaseCalls"
        # non-BAM/VCF files from the Alignment folder
        newalignmentdir = newfastqdir / "Alignment"

        print(f"INFO: Creating new folder {newdatadir}", file=sys.stderr)

        # Try to create the new analyis folder (e.g. /Myeloid_1.2)
        # If this already exists we want to halt - should not be overwritten
        try:
            newdatadir.mkdir(parents=True)
        except FileExistsError:
            print(
                "INFO: The run folder already exists, but existing files should not be replaced by this script.",
                file=sys.stderr,
            )
        # Don't overwrite an existing analysis folder - print a message and exit
        try:
            # This makes the alignment folder, which will only exist if it's
            # been previously analysed so this one *should* give an error
            newalignmentdir.mkdir(parents=True, exist_ok=True)
        except FileNotFoundError:
            print(
                f"ERROR: Could not create folder {newalignmentdir} due to missing or inaccessible parent",
                file=sys.stderr,
            )
            sys.exit(1)

        # Use the list of file types in the config file and glob all matching
        # files in the data directory, then use shutil.copyfile to copy
        # (NOT move) to the target directory (newdatadir)
        for filetype in config["directories"].getlist("filetypes"):
            for oldfile in datadir.glob(filetype):
                print(f"INFO: Moving {oldfile.name}", file=sys.stderr)
                newfile = newdatadir / oldfile.name

                # DEV: I don't know all the ways in which this might go wrong,
                # so I'll rely on it just dying and raising an exception.
                # I doubt I will want to handle them any other way than just
                # exiting, but I might want to add a more friendly error
                # message.
                quickcopy(oldfile, newfile)

        # Copy the Sample Sheet and the AmpliconCoverage file
        # DEV: As above, this could go wrong in a few ways. Once these are
        # known, add handlers These should also go to the new alignment folder
        quickcopy(datadir / "SampleSheetUsed.csv", newrundir / "SampleSheetUsed.csv")
        quickcopy(
            datadir / "SampleSheetUsed.csv", newalignmentdir / "SampleSheetUsed.csv"
        )
        quickcopy(
            datadir / "AmpliconCoverage_M1.tsv",
            newrundir / "AmpliconCoverage_M1.tsv",
        )
        quickcopy(
            datadir / "AmpliconCoverage_M1.tsv",
            newalignmentdir / "AmpliconCoverage_M1.tsv",
        )
        # DEV: This file does not exist in LRM runs - handle missing
        try:
            quickcopy(
                datadir / "DemultiplexSummaryF1L1.txt",
                newrundir / "DemultiplexSummaryF1L1.txt",
            )
            quickcopy(
                datadir / "DemultiplexSummaryF1L1.txt",
                newalignmentdir / "DemultiplexSummaryF1L1.txt",
            )
        except FileNotFoundError:
            # These files don't exist in LRM-style runs
            pass
        # There are also a couple of MiSeq files to be moved (to match
        # panels, I'm not sure if they're essential for repeating this)
        quickcopy(rundir / "RunInfo.xml", newrundir / "RunInfo.xml")
        quickcopy(rundir / "RunParameters.xml", newrundir / "RunParameters.xml")

        quickcopy(
            rundir / "TruSight-Myeloid-Manifest.txt",
            newrundir / "TruSight-Myeloid-Manifest.txt",
        )

        # Copy the InterOp folder to the backup drive
        # To copy a folder and it's files & subfolders, use shutil copytree()
        copytree(
            rundir / "InterOp",
            newrundir / "InterOp",
            dirs_exist_ok=True,
            copy_function=quickcopy,
        )

        # Copy the fastqs and the remaining folders so that the new data
        # directory is more in line with the setup of the panels and genotyping
        # folder. Create the Data directory regardless of fast copying
        if config.getboolean("general", "copy_fastqs"):
            print(f"INFO: Copying fastq files in {basecallsdir}", file=sys.stderr)
            for oldfile in basecallsdir.glob("*.fastq.gz"):
                print(f"INFO: Moving {oldfile.name}", file=sys.stderr)
                newfile = newfastqdir / oldfile.name
                quickcopy(oldfile, newfile)

        # If the option is set, copy the BAM files to the temporary BAM file
        # store
        if config.getboolean("general", "copy_bams"):
            # First, create the run folder in the temp store
            try:
                # Add the run ID to the BAM store path
                bamstore = Path(f"{config.get('directories', 'bam-store-dir')}\\{runid}")
                bamstore.mkdir(parents=True, exist_ok=True)
            except FileNotFoundError:
                print(
                    f"ERROR: Could not create folder {bamstore} due to missing or inaccessible parent",
                    file=sys.stderr,
                )
                sys.exit(1)

            # Copy the BAM and BAI files to the temp store
            for oldfile in datadir.glob("*.ba*"):
                print(f"INFO: Moving {oldfile.name} to temporary BAM store",
                      file=sys.stderr
                     )
                newfile = bamstore / oldfile.name
                quickcopy(oldfile, newfile)

        # Return the new run data, so we can then use that to call the coverage
        # module
        return newdatadir

    @staticmethod
    def get_details_tk(datadir: str = None) -> tuple:
        """
        Opens file picker dialogues from tkinter if there is no command line input.

        Taret directory should be imputed from the run ID and the path set in the
        config file, not using a second file picker.
        """

        # If there is no datadir given, open a file picker to allow the user to
        # to choose.
        if not datadir:
            root = tk.Tk()

            # Select the source run folder
            root.filename = filedialog.askdirectory(
                title="Select run folder",
                initialdir=config.get("directories", "source-dir"),
            )

            # If the dialogue is closed, the program will raise an exception
            # and a confusing error. Instead, display a simple message and quit
            # more gracefully.
            try:
                rootdir = Path(root.filename)
            except TypeError:
                print("ERROR: No run folder selected.", file=sys.stderr)
                sys.exit(1)

            root.withdraw()

            datadir = rootdir/"Data"/"Intensities"/"BaseCalls"/"Alignment"

        # Ensure that the data directory is a Path object
        datadir = Path(datadir)

        # Ensure that the Alignment folder exists within the run folder.
        # If it doesn't, the sequencing may not yet be complete, or it may
        # be a more recent LRM-style run. Check this first, then error if still
        # not found
        if not datadir.is_dir():
            # For an LRM run, find the first analyis and the first repeat of
            # that analysis - this would be tricky to do any other way right
            # now. Best option might be to check for BAM files in the folder,
            # so the user can manually select the analysis they want, rather
            # than only selecting the run folder?

            # Get the latest alignment folder (e.g. most recent settings in 
            # case of a re-analysis)
            datadirs = rootdir.glob("Alignment_*")
            datadir = [x for x in datadirs][-1]
            # Get the latest subfolder (i.e. re-analysis with the same settings)
            subfolders = [folder for folder in datadir.iterdir() if folder.is_dir()]
            datadir = subfolders[-1]

            if not datadir.is_dir():
                print(
                    "ERROR: Target directory does not have an 'Alignment' folder",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Set the destination folder
        networkdir = config.get("directories", "target-dir")

        # DEV: Just for now return the defaults
        targetdir = Path(networkdir)

        # Return the two paths
        return (datadir, targetdir)
