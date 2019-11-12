# Myeloid panel backup script

## Purpose

When given a myeloid run folder, this script should automatically
transfer the relevant run data (VCF, BAM, BAI, etc.) from the MiSeq
runfolder to the Z: drive so it can be accessed via the Trust
network.

## Usage

### General usage

To use the script, just double-click on the shortcut (this can be moved wherever required, as long as the W: network drive is availble). A dialogue box will open to choose the run folder you want to move, then another will open to confirm or select the folder you wish to move it to.

### Changing directory

The target directory is defined in the transfer.config file. To change the default target directory, just update this file. To change the target as a one-off, just select the required folder in the folder picker dialogue box that opens when the program runs.

## Installation

### pyinstaller installation

The script can be intalled to and then run from a single executable file using pyinstaller.

Pyinstaller and all other dependencies are listed in requriements.txt and can be installed to
a standard python virtualenv. This virtualenv is not needed to run the final .exe

The MyeloidTransfer.spec file has been modified so that transfer.config is copied into the dist
folder and accessed by the executable from the dist folder, rather than packaged into the exe.
This means that the config settings can now be edited by the user from this file.

If you make any changes, the executable will need to be rebuilt. This is simple using the
spec file, just run (to use the venv python)

`python -m PyInstaller --clean MyeloidTransfer.spec`

### Distribution

All neessary files are in the dist folder. This can be copied to wherever it is needed.
It can also be renamed however you want, as can the .exe. transfer.config needs to keep the same name.

I recommend providing a shortcut to the main exe to users, and ensuring that both it and
transfer.config are kept as read only unless you need to edit them.
