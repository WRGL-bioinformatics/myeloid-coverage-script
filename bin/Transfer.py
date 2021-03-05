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
from bin.QuickCopy import quickcopy


class MyeloidTransfer(object):
    def __init__(self, datadir: str = None):
        # Get the run folder and target folder
        print(
            "INFO: Default source directory: {}".format(
                config.get("directories", "source-dir")
            )
        )
        print(
            "INFO: Default target directory: {}".format(
                config.get("directories", "target-dir")
            )
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
        print("INFO: Selected run folder: {}".format(datadir), file=sys.stderr)
        print(
            "INFO: Selected destination folder: {}".format(targetdir), file=sys.stderr
        )

        # Extract the run ID from the data folder path
        # Since the MiSeq data directory structure is fixed, we know exactly
        # which section of the path has this, but we have to go from the end as
        # there could be changes before
        runid = datadir.parts[-5]

        # datadir is the alignment folder
        # For some of this we will need the BaseCalls folder above it
        basecallsdir = datadir.parent
        # And for some we will need the root run folder
        rundir = basecallsdir.parent.parent.parent

        # Create new folder in the target directory
        newrundir = targetdir / runid
        # this is the folder to hold the bams/vcfs
        newdatadir = newrundir / "Myeloid_{}".format(config.get("general", "version"))
        # For Fastq backup
        newfastqdir = newrundir / "Data" / "Intensities" / "BaseCalls"
        # non-BAM/VCF files from the Alignment folder
        newalignmentdir = newfastqdir / "Alignment"

        print("INFO: Creating new folder {}".format(newdatadir), file=sys.stderr)

        # Try to create the new runfolder
        # Don't overwrite an existing folder - print a message and exit
        try:
            newdatadir.mkdir(parents=True)
            newalignmentdir.mkdir(parents=True)
        except FileExistsError:
            print(
                "ERROR: The run folder {} already exists".format(newdatadir),
                file=sys.stderr,
            )
            sys.exit(1)
        except FileNotFoundError:
            print(
                "ERROR: Could not create folder {} due to missing or inaccessible parent".format(
                    newdatadir
                ),
                file=sys.stderr,
            )
            sys.exit(1)

        # Use the list of file types in the config file and glob all matching
        # files in the data directory, then use shutil.copyfile to copy (NOT move)
        # to the target directory (newdatadir)
        for filetype in config["directories"].getlist("filetypes"):
            for f in datadir.glob(filetype):
                print("INFO: Moving {}".format(f.name), file=sys.stderr)
                newfile = newdatadir / f.name

                # DEV: I don't know all the ways in which this might go wrong, so I'll rely on it
                # just dying and raising an exception. I doubt I will want to handle them any
                # other way than just exiting, but I might want to add a more friendly error
                # message.
                quickcopy(f, newfile)

        # Copy the Sample Sheet and the AmpliconCoverage file
        # DEV: As above, this could go wrong in a few ways. Once these are known, add handlers
        # These should also go to the new alignment folder
        quickcopy(datadir / "SampleSheetUsed.csv", newrundir / "SampleSheetUsed.csv")
        quickcopy(
            datadir / "SampleSheetUsed.csv", newalignmentdir / "SampleSheetUsed.csv"
        )
        quickcopy(
            datadir / "AmpliconCoverage_M1.tsv", newrundir / "AmpliconCoverage_M1.tsv",
        )
        quickcopy(
            datadir / "AmpliconCoverage_M1.tsv",
            newalignmentdir / "AmpliconCoverage_M1.tsv",
        )
        quickcopy(
            datadir / "DemultiplexSummaryF1L1.txt",
            newrundir / "DemultiplexSummaryF1L1.txt",
        )
        quickcopy(
            datadir / "DemultiplexSummaryF1L1.txt",
            newalignmentdir / "DemultiplexSummaryF1L1.txt",
        )
        # There are also a couple of MiSeq files that need to be moved (to match
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

        # TODO
        # Copy the fastqs and the remaining folders so that the new data directory is
        # more in line with the setup of the panels and genotyping folder
        # Create the Data directory regardless of fast copying
        if config.getboolean("general", "copy_fastqs") == True:
            print(
                "INFO: Copying fastq files in {}".format(basecallsdir), file=sys.stderr
            )
            for f in basecallsdir.glob("*.gz"):
                print("INFO: Moving {}".format(f.name), file=sys.stderr)
                newfile = newfastqdir / f.name
                quickcopy(f, newfile)

        # Return the new run data, so we can then use that to call the coverage module
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
        if datadir == None:
            root = tk.Tk()

            # Select the source run folder
            root.filename = filedialog.askdirectory(
                title="Select run folder",
                initialdir=config.get("directories", "source-dir"),
            )

            # If the dialogue is closed, the program will raise an exception and a
            # confusing error. Instead, display a simple message and quit more
            # gracefully.
            try:
                rootdir = Path(root.filename)
            except TypeError:
                print("ERROR: No run folder selected.", file=sys.stderr)
                sys.exit(1)

            root.withdraw()

            datadir = rootdir / "Data" / "Intensities" / "BaseCalls" / "Alignment"

        # Ensure that the data directory is a Path object
        datadir = Path(datadir)

        # Ensure that the Alignment folder exists within the run folder.
        # If it doesn't, the sequencing may not yet be complete.
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
