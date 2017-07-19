# -*- coding: utf-8 -*-
import StringIO
import re
import csv
import os
import logging
l = logging.getLogger("mapdataloader")

__author__ = 'carlos.coelho'


class MapDataLoader(object):
    """ Provides the raw data for a Map() object to work in, abstracting filesystem/fileformat from the Map itself.
    """
    def __init__(self, _filename):

        # This map matches os.path.basename(filename) against the specific data loaders supported by this module.
        self.loadabletypes = {# Ignore opened .xlsx backups
                                r"^\~\$.+\.xlsx$": self.noneloader,
                              # XLSX Loader
                                r"\.xlsx$": self.xlsxloader,
                              # CSV Loader
                                r"\.csv$": self.csvloader }


        # Save the filename
        self.filename = _filename

    # --------------
    # load() funcion
    # --------------

    def load(self):
        # Try to find a suitable loader for this filename.
        # noneloader is the default loaderfunc (which does nothing), in case nothing gets matched by the regexps.
        loaderfunc = self.noneloader
        for fnregexp in self.loadabletypes.keys():
            basefn = os.path.basename(self.filename)
            if re.search(fnregexp, basefn):
                loaderfunc = self.loadabletypes[fnregexp]
                l.debug(u"Arquivo %s será processado pelo módulo \"%s\"" % (basefn, loaderfunc.__name__))
                break

        # Call loaderfunc with filename as param, return its output value [data as a list] to outside.
        return loaderfunc(self.filename)

    # --------------
    # Custom Loaders
    # --------------

    def noneloader(self,fn):
        return []

    def xlsxloader(self, fn):
        try:
            from openpyxl import load_workbook
            import warnings
        except:
            print "Please install python module OPENPYXL to enable .XLSX Map import."
            return []

        # Load XLSX
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            wb = load_workbook(fn)
            # Load FIRST SHEET (This is the sheet that will be used to extract data)
            ws = wb.get_sheet_by_name(wb.get_sheet_names()[0])

        celldata = []
        # Extract data.
        for row in ws.rows:
            celldata.append([unicode(cell.value if cell.value else u'') for cell in row])

        return celldata

    def csvloader(self, fn):
        def getmapdata(_mapfn):
            with open(_mapfn, 'rb') as mapfo:
                mapdata = mapfo.read()

            return StringIO.StringIO(mapdata)

        mapfileobj = getmapdata(fn)
        csvf = csv.reader(mapfileobj, dialect='excel', delimiter=";", quotechar='"')

        return [csvline for csvline in csvf]