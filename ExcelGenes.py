# genedict defines each subpanel and where in the report it should be placed.
# 'column' and 'row' indicate the start positions of each section.
# column uses a numerical indicator rather than letters, and this is 0 indexed
# All headers span two columns.
# Below are the genes and the percentages to 2dp including a percentage sign
# Headers in row 1 are 1 cell deep, any others are 2 rows deep and merged.

genedict = {
    "RAS/TK Signalling": {
        "column": 0,
        "row": 0,
        "genes": [
            "BRAF",
            "CALR",
            "CBL",
            "CBLB",
            "CSF3R",
            "FLT3",
            "HRAS",
            "JAK2",
            "JAK3",
            "KIT",
            "KRAS",
            "MPL",
            "NRAS",
            "PDGFRA",
            "PTPN11",
        ],
    },
    "Other signalling pathway genes": {
        "column": 2,
        "row": 0,
        "genes": ["MYD88", "NOTCH1", "PTEN"],
    },
    "DNA/chromatin modificiation": {
        "column": 2,
        "row": 4,
        "genes": [
            "ASXL1",
            "ATRX",
            "BCOR",
            "BCORL1",
            "DNMT3A",
            "EZH2",
            "GATA1",
            "IDH1",
            "IDH2",
            "KMT2A",
            "PHF6",
            "TET2",
        ],
    },
    "Cohesin pathway": {
        "column": 4,
        "row": 0,
        "genes": ["RAD21", "SMC1A", "SMC3", "STAG2"],
    },
    "Transcription factors": {
        "column": 4,
        "row": 5,
        "genes": ["CUX1", "ETV6", "GATA2", "IKZF1", "RUNX1", "WT1"],
    },
    "Splicing pathway": {
        "column": 6,
        "row": 0,
        "genes": ["SF3B1", "SRSF2", "U2AF1", "ZRSR2"],
    },
    "Other": {"column": 6, "row": 5, "genes": ["FBXW7", "NPM1", "SETBP1", "TP53"]},
    "Hotspot coverage (100x)": {
        "column": 10,
        "row": 0,
        "genes": [
            "NRAShotspot12&13",
            "DNMT3AhotspotR882",
            "SF3B1hotspotK700",
            "SF3B1hotspotH662K666",
            "SF3B1hotspotE622N626",
            "IDH1hotspotR132",
            "KIThotspotD816V",
            "NPM1hotspot",
            "JAK2hotspotexon12",
            "JAK2hotspotV617F",
            "HRAShotspot61",
            "HRAShotspot12&13",
            "CBLhotspotC381R420",
            "KRAShotspot61",
            "KRAShotspot12&13",
            "IDH2hotspotR172",
            "SRSF2hotspotP95",
            "SETBP1hotspot868880",
            "U2AF1hotspotQ157",
            "U2AF1hotspotS34",
            "IDH2hotspotR140",
        ],
    },
}

# boldgenes defines the list of genes that should have BOLD formatting in the report
boldgenes = [
    "BCOR",
    "BCORL1",
    "DNMT3A",
    "EZH2",
    "PHF6",
    "RAD21",
    "STAG2",
    "CUX1",
    "ETV6",
    "IKZF1",
    "RUNX1",
    "ZRSR2",
]
