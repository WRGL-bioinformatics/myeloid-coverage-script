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
            f"INFO: No target folder specified. Opening file selector...",
            file=sys.stderr,
        )
        transfer = MyeloidTransfer()

    # Now process the coverage information for this run
    # Automatically writes an Excel workbook as output
    coverage = MyeloidCoverage(transfer.newdatadirectory)
