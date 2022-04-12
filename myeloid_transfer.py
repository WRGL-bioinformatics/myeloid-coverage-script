"""
Author: Ben.Sanders@NHS.net

Main function to run the Myeloid data transfer and coverage report generation
"""
import sys
from bin.Transfer import MyeloidTransfer
from bin.Coverage import MyeloidCoverage

if __name__ == "__main__":
    # Transfer run folders from the MiSeq to the Z: drive
    # This handles asking for folders, transferring data, etc.
    try:
        transfer = MyeloidTransfer(sys.argv[1])
    # If no folder arg is given, this will raise an IndexError
    # Handle only this, so that any other errors will still raise
    except IndexError:
        print(
            "INFO: No target folder specified. Opening file selector...",
            file=sys.stderr,
        )
        try:
            transfer = MyeloidTransfer()
        except FileNotFoundError:
            # Message and quit if no valid folder selected
            print("WARNING: Either no target directory selected or it does not contain an Alignment folder.",
                  file=sys.stderr)
            sys.exit(0)

    # Now process the coverage information for this run
    # Automatically writes an Excel workbook as output
    coverage = MyeloidCoverage(transfer.newdatadirectory)
