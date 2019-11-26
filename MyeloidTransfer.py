from bin.Transfer import MyeloidTransfer
from bin.Coverage import MyeloidCoverage

if __name__ == "__main__":
    # Transfer run folders from the MiSeq to the Z: drive
    # This handles asking for folders, transferring data, etc.
    transfer = MyeloidTransfer()
    newdatadir = transfer.newdatadirectory

    # Now process the coverage information for this run
    # Automatically writes an Excel workbook as output
    coverage = MyeloidCoverage(newdatadir)
