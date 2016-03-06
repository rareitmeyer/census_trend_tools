# Take a bunch of zip files named like the below...
#     acs_non_places_2005_0-40.zip   acs_non_places_2014_41-46.zip
#     acs_non_places_2005_41-60.zip  acs_non_places_2014_47-61.zip
#     acs_non_places_2006_0-40.zip   acs_places_2005_0-40.zip
#     acs_non_places_2006_41-64.zip  acs_places_2005_41-67.zip
#     acs_non_places_2007_0-40.zip   acs_places_2006_0-40.zip
#     acs_non_places_2007_41-64.zip  acs_places_2006_41-71.zip
#     acs_non_places_2008_0-40.zip   acs_places_2007_0-40.zip
#     acs_non_places_2008_41-62.zip  acs_places_2007_41-71.zip
#     acs_non_places_2009_0-40.zip   acs_places_2008_0-40.zip
#     acs_non_places_2009_41-61.zip  acs_places_2008_41-69.zip
#     acs_non_places_2010_0-40.zip   acs_places_2009_0-40.zip
#     acs_non_places_2010_41-50.zip  acs_places_2009_41-61.zip
#     acs_non_places_2010_51-56.zip  acs_places_2010_0-40.zip
#     acs_non_places_2011_0-40.zip   acs_places_2010_41-56.zip
#     acs_non_places_2011_41-50.zip  acs_places_2011_0-40.zip
#     acs_non_places_2011_51-56.zip  acs_places_2011_41-56.zip
#     acs_non_places_2012_0-40.zip   acs_places_2012_0-40.zip
#     acs_non_places_2012_41-54.zip  acs_places_2012_41-60.zip
#     acs_non_places_2012_55-60.zip  acs_places_2013_0-40.zip
#     acs_non_places_2013_0-40.zip   acs_places_2013_41-61.zip
#     acs_non_places_2013_41-54.zip  acs_places_2014_0-40.zip
#     acs_non_places_2013_55-60.zip  acs_places_2014_41-69.zip
#     acs_non_places_2014_0-40.zip
# And burst them into files in directory tree
#     acs/
#       places/
#         2005
#         2006
#         ...
#       non_places
#         2005
#         ...

import os
import sys
import logging
import time
import re
import zipfile
import shutil

NOW = time.time()

if not os.path.exists("logs"):
    os.mkdir("logs")

logging.basicConfig(
    filename=os.path.join("logs",__file__+time.strftime('.%Y%m%d_%H%M%S.log', time.localtime(NOW))),
    format='%(asctime)|%(levelno)|%(levelname)|%(filename)|%(lineno)|%(message)',
    level=logging.DEBUG
    )

def parse_zipfilename(filename):
    basename = os.path.basename(filename)
    m = re.search('acs_(?P<type>(non_places)|(places))_(?P<year>[0-9]*)_(?P<table_range>[0-9-]*)\\.zip', basename)
    retval = {}
    if m:
        retval = {
            'type': m.group('type'),
            'year': int(m.group('year')),
            'table_range': m.group('table_range'),
            }
    return retval
    

def burst(topdir='.', raw_dir='raw'):
    acs_dir = os.path.join(topdir, 'acs')
    if os.path.exists(acs_dir):
        # Move old work aside
        shutil.move(acs_dir, acs_dir+time.strftime('_%Y%m%d_%H%M%S', time.localtime(NOW)))
    os.mkdir(acs_dir, mode=0o755)
    for (dirpath, dirnames, filenames) in os.walk(raw_dir):
        for fn in filenames:
            fullpath = os.path.join(dirpath, fn)
            zinfo = parse_zipfilename(fn)
            if zinfo != {}:
                type_dir = os.path.join(acs_dir, zinfo['type'])
                year_dir = os.path.join(type_dir, str(zinfo['year']))
                if not os.path.exists(type_dir):
                    os.mkdir(type_dir, mode=0o755)
                if not os.path.exists(year_dir):
                    os.mkdir(year_dir, mode=0o755)
                with zipfile.ZipFile(fullpath, 'r') as zip:
                    # sanity check the zip file
                    names = zip.namelist()
                    for n in names:
                        assert not n.startswith('/')
                        assert n.find('..') == -1
                    # extract all files.
                    zip.extractall(path=year_dir)
                

if __name__ == '__main__':
    burst()
