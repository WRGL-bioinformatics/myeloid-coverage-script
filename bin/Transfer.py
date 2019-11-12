"""
Myeloid automatic file transfer
===============================

Author: ben.sanders@nhs.net

purpose
-------

Allow the user to select a run folder containing a myeloid
sequencing run, then 

"""
import sys
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from shutil import copyfile

# config is shared across multiple classes, so we load it up in its own module
# to avoid repetition of the config parsing code
from bin.Config import config


class MyeloidTransfer(object):
    def __init__(self):
        # Get the run folder and target folder
        print("INFO: Default source directory: {}".format(config.get("directories", "source-dir")))
        print("INFO: Default target directory: {}".format(config.get("directories", "target-dir")))
        datadir, targetdir = self.get_details_tk()
        self.newdatadir = self.transfer_files(datadir, targetdir)

    @property
    def newdatadirectory(self):
        """Return the new data directory target for copying"""
        return self.newdatadir

    def transfer_files(self, datadir: str, targetdir: str) -> str:
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

        # Create new folder in the target directory
        newdatadir = targetdir / runid
        print("INFO: Creating new folder {}".format(newdatadir), file=sys.stderr)

        # Try to create the new runfolder
        # Don't overwrite an existing folder - print a message and exit
        try:
            newdatadir.mkdir()
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

        # TODO
        # DEV:
        # Copy the fastqs and the remaining folders so that the new data directory is
        # more in line with the setup of the panels and genotyping folder

        # Now we can add a Myeloid_panel folder for the remaining files, to match the
        # structure of panels and genotyping
        newdatadir = newdatadir / "Myeloid_1.0"
        # Use the list of file types in the config file and glob all matching
        # files in the data directory, then use shutil.copyfile to copy (NOT move)
        # to the target directory (newdatadir)
        for filetype in config["directories"].getlist("filetypes"):
            for f in datadir.glob(filetype):
                print("INFO: Moving {}".format(f.name), file=sys.stderr)
                newfile = newdatadir / f.name

                # I don't know all the ways in which this might go wrong, so I'll rely on it
                # just dying and raising an exception. I doubt I will want to handle them any
                # other way than just exiting, but I might want to add a more friendly error
                # message.
                copyfile(f, newfile)

        # Return the new run data, so we can then use that to call the coverage module
        return newdatadir

    def get_details_tk(self) -> tuple:
        """
        Opens file picker dialogues from tkinter
        """
        print("Trying to open file picker dialog...", file=sys.stderr)
        root = tk.Tk()

        # Select the source run folder
        root.filename = filedialog.askdirectory(
            title="Select run folder",
            initialdir=config.get("directories", "source-dir"),
        )

        # If the dialogue is closed, the program will raise an exception and a confusing
        # error. Instead, display a simple message and quit more gracefully.
        try:
            rootdir = Path(root.filename)
        except TypeError:
            print("ERROR: No run folder selected.", file=sys.stderr)
            sys.exit(1)

        datadir = rootdir / "Data" / "Intensities" / "BaseCalls" / "Alignment"

        # Ensure that the Alignment folder exists within the run folder.
        # If it doesn't, the sequencing may not yet be complete.
        if not datadir.is_dir():
            print(
                "ERROR: Target directory does not have an 'Alignment' folder",
                file=sys.stderr,
            )
            sys.exit(1)

        # Select the destination folder
        # if this filepicker is cancelled, targetdir seems to get the script directory.
        # This isn't what I want, so hopefully this will solve it and it will default
        # to the target directory from config.
        targetdir = config.get("directories", "target-dir")
        root.filename = filedialog.askdirectory(
            title="Select destination",
            initialdir=config.get("directories", "target-dir"),
        )
        try:
            targetdir = Path(root.filename)
        except TypeError:
            print("ERROR: No target folder selected.", file=sys.stderr)
            sys.exit(1)

        root.withdraw()

        # Return the two paths
        return (datadir, targetdir)

    def check_runfolder(self, path: str):
        """
        Check that the selected run folder appears to hold a myeloid panel run, not any
        other type of run that should automatically transfer during the standard pipeline.
        """
        pass
        # TODO
