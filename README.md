# fronius_pvtracker
Small PV-Tracker running on a raspberry pi 3b+, showing main data from a fronius inverter in the same LAN.

It consists of a simple wrapper for [Fronius Solar API v1.0](https://www.fronius.com/de/solarenergie/produkte/alle-produkte/anlagen-monitoring/offene-schnittstellen/fronius-solar-api-json-), RequestReader.py,
that is use with a tkinter-frontend via the RequestController.
On start the FroniusScanner will scan the IP range defined in config.ini for available Fronius inverters.

