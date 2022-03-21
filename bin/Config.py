"""
Author: Ben.Sanders@NHS.net

Create the ConfigParse, so we don't duplicate this in multiple modules.
"""

import sys
from configparser import ConfigParser
from pathlib import Path

# Use a list converted to allow easy parsing of comma separated lists from
# the config file using config[<section>].getlist(<listname>)
config = ConfigParser(converters={"list": lambda x: [i.strip() for i in x.split(",")]})

# Ironically the config filename has to be hardcoded here

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS', byt sys.executable seems to work better.
    application_path = Path(sys.executable).parent
else:
    # If not frozen, we need to redirect to the 'static' folder
    application_path = Path(__file__).parent.parent.joinpath("static")

# Now we can read the config file, regardless of the folder the script is run from
config.read(application_path / "transfer.config")
