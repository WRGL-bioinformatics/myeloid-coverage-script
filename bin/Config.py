"""
Author: Ben.Sanders@NHS.net

Create the ConfigParse, so we don't duplicate this in multiple modules.
"""

from configparser import ConfigParser

# Use a list converted to allow easy parsing of comma separated lists from 
# the config file using config[<section>].getlist(<listname>)
config = ConfigParser(converters={"list": lambda x: [i.strip() for i in x.split(",")]})

# Ironically the config filename has to be hardcoded here
config.read("transfer.config")
