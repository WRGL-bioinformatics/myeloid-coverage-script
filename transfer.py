"""
Myeloid automatic file transfer
===============================

Author: ben.sanders@nhs.net

purpose
-------

Allow the user to select a run fodler containing a myeloid
sequencing run, then 

"""
import sys
import tkinter as tk
from tkinter import filedialog
from configparser import ConfigParser
from pathlib import Path
from shutil import copyfile


def transfer_files(config):
    print(
        "INFO: Source folder: {}".format(config.get("directories", "source-dir")),
        file=sys.stderr,
    )
    print(
        "INFO: Target folder: {}".format(config.get("directories", "target-dir")),
        file=sys.stderr,
    )

    # Get the run folder and target folder
    datadir, targetdir = get_details_tk(config)

    print("INFO: Selected run folder: {}".format(datadir), file=sys.stderr)
    print("INFO: Selected destination folder: {}".format(targetdir), file=sys.stderr)

    # TODO - check that the run seems to be a myeloid panel

    # Extract the run ID from the data folder path
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

    # Copy the necessary files
    for filetype in ['*.bam', '*.bai', '*.vcf', '*.idx']:
        for f in datadir.glob(filetype):
            print("INFO: Moving {}".format(f.name), file=sys.stderr)
            newfile = newdatadir / f.name
            # I don't know all the ways in which this might go wrong, so I'll rely on it
            # just dying and raising an exception. I doubt I will want to handle them any
            # other way than just exiting, but I might want to add a more friendly error 
            # message.
            copyfile(f, newfile)

def get_details_tk(config):
    """
    Opens file picker dialogues from tkinter
    """
    print("Trying to open file picker dialog...", file=sys.stderr)
    root = tk.Tk()
    # Select the source run folder
    root.filename = filedialog.askdirectory(
        title="Select run folder", initialdir=config.get("directories", "source-dir")
    )

    rootdir = Path(root.filename)
    datadir = rootdir / "Data" / "Intensities" / "BaseCalls" / "Alignment"

    # Ensure that the Alignment folder exists within the run folder.
    # If it doesn't, the sequencing may not yet be complete.
    assert (
        datadir.is_dir()
    ), "ERROR: Target directory does not have an 'Alignment' folder"

    # Select the destination folder
    root.filename = filedialog.askdirectory(
        title="Select destination", initialdir=config.get("directories", "target-dir")
    )
    targetdir = Path(root.filename)

    # Return the two paths
    return (datadir, targetdir)


def check_runfolder(path: str):
    """
    Check that the selected run folder appears to hold a myeloid panel run, not any
    other type of run that should automatically transfer during the standard pipeline.
    """
    pass
    # TODO


if __name__ == "__main__":
    # Read the config file into the config object
    config = ConfigParser()
    config.read("transfer.config")
    # Start the transfer process
    transfer_files(config)
