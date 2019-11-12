from bin.Transfer import MyeloidTransfer
from bin.Coverage import MyeloidCoverage

if __name__ == "__main__":
    # Transfer run folders from the MiSeq to the Z: drive
    # This handles asking for folders, transferring data, etc.
    transfer = MyeloidTransfer()
    newdatadir = transfer.newdatadirectory

    #newdatadir="/home/genetics/Documents/DEV/python_myeloid_coverage/TESTDATA/TARGET/191018_M01875_0514_000000000-CM7GG/"
    # Now process the coverage information for this run
    # Automatically writes an Excel workbook as output
    coverage = MyeloidCoverage(newdatadir)
