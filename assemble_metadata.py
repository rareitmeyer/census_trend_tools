# Suppose you have a lot of American Fact Finder data files,
# named like "ACS_10_5YR_S1901_with_ann.csv" and "ACS_10_5YR_S1901_metadata.csv"
# Because the column names (both long and short) change from year to year,
# this tool will bring together all of the metadata into a single file for
# subsequent searching.
#
# EG, ACS_YEAR, FILENAME, SHORTCOLNAME, LONGCOLNAME

# Requires Python3.

# Copyright R. A. Reitmeyer
# Released under the GNU Public License, version 2, or later.

import os
import sys
import logging
import csv
import time
import re

NOW = time.time()

if not os.path.exists("logs"):
    os.mkdir("logs")

logging.basicConfig(
    filename=os.path.join("logs",__file__+time.strftime('.%Y%m%d_%H%M%S.log', time.localtime(NOW))),
    format='%(asctime)|%(levelno)|%(levelname)|%(filename)|%(lineno)|%(message)',
    level=logging.DEBUG
    )


def parse_ACS_filename(filename):
    """Take a ACS filename and return a dict with the details of the file:
    ACS (final) year of the data, the number of years the data spans,
    the table name, and what kind of file it is.

    >>> parse_ACS_filename("ACS_14_1YR_S0902_with_ann.csv") == {'year': 2014, 'span': 1, 'table': 'S0902', 'kind': '_with_ann.csv'}
    True
    >>> parse_ACS_filename("ACS_14_1YR_S0902_metadata.csv") == {'year': 2014, 'span': 1, 'table': 'S0902', 'kind': '_metadata.csv'}
    True
    >>> parse_ACS_filename("ACS_14_1YR_S0902.txt") == {'year': 2014, 'span': 1, 'table': 'S0902', 'kind': '.txt'}
    True
    >>> parse_ACS_filename("ACS_14_1YR_S0902PR_with_ann.csv") == {'year': 2014, 'span': 1, 'table': 'S0902PR', 'kind': '_with_ann.csv'}
    True
    >>> parse_ACS_filename("unrecognized_file.csv") == {}
    True
    >>> parse_ACS_filename("ACS_05_EST_S0701_metadata.csv") == {'year': 2005, 'span': '', 'table': 'S0701', 'kind': '_metadata.csv'}
    True
    """
    basename = os.path.basename(filename)
    m = re.search('ACS_(?P<year>[0-9][0-9])_(?P<span>[0-9])YR_(?P<table>[A-Z0-9]+)(?P<kind>(_metadata\\.csv)|(\\.txt)|(_with_ann\\.csv))', basename)
    retval = {}
    if m:
        retval = {
            'year': 2000+int(m.group('year')),
            'span': int(m.group('span')),
            'table': m.group('table'),
            'kind': m.group('kind'),
            }
    else:
        # Try an older format
        m = re.search('ACS_(?P<year>[0-9][0-9])_EST_(?P<table>[A-Z0-9]+)(?P<kind>(_metadata\\.csv)|(\\.txt)|(_with_ann\\.csv))', basename)
        if m:
            retval = {
                'year': 2000+int(m.group('year')),
                'span': '', # ? don't know span
                'table': m.group('table'),
                'kind': m.group('kind'),
                 }
    return retval


def burst_name(longname):
    """Burst the long name into (up to four) parts.
    EG: 
      Estimate; Total population - SEX AND AGE - Female
    should turn into 
       EST_OR_MARGIN = Estimate
       NAME = Total population - SEX AND AGE - Female
    
    And
    Foreign born; Born in Europe; Estimate; Civilian employed population 16 years and over - OCCUPATION - Production, transportation, and material moving occupations
    should become:
       EST_OR_MARGIN = Estimate
       NAME = Civilian employed population 16 years and over - OCCUPATION - Production, transportation, and material moving occupations
       ROLLUP1 = Foreign Born
       ROLLUP2 = Born in Europe
    """
    retval = {}
    if longname.find(';') != -1:
        burst_name = [f.strip() for f in longname.split(';')]
        retval['NAME'] = burst_name[-1]
        retval['EST_OR_MARGIN'] = burst_name[-2]
        if len(burst_name) == 3:
            retval['ROLLUP1'] = burst_name[0]
        if len(burst_name) == 4:
            retval['ROLLUP1'] = burst_name[0]
            retval['ROLLUP2'] = burst_name[1]
    return retval


def assemble_metadata(topdir='acs', output_filename='all_metadata.csv'):
    """Assemble all of the metadata from the _metadata files under the
    top level directory. Assumption is that you have a big tree of 
    American Fact Finder data named like "ACS_10_5YR_S1901_with_ann.csv"
    and "ACS_10_5YR_S1901_metadata.csv"
    
    The goal is to assemble a complete set of metadata across all files
    that can be searched for common names.
    """
    with open(output_filename, 'w', encoding='utf-8', newline='') as out_fp:
        writer = csv.writer(out_fp)
        name_details = ["EST_OR_MARGIN", "NAME", "ROLLUP1", "ROLLUP2"]
        header = ['FILENAME', 'ACS_YEAR', 'ACS_SPAN', 'TABLE', 'SHORTCOLNAME', 'LONGCOLNAME']
        writer.writerow(header + name_details)
        for (dirpath, dirnames, filenames) in os.walk(topdir):
            dirnames.sort()
            filenames.sort()
            for fn in filenames:
                acs = parse_ACS_filename(fn)
                if acs.get('kind', '') == '_metadata.csv':
                    with_ann_fn = re.sub('_metadata', '_with_ann', fn)
                    with open(os.path.join(dirpath, fn), 'r', encoding='utf-8') as in_fp:
                        reader = csv.reader(in_fp)
                        for row in reader:
                            details = burst_name(row[1])
                            output_row = [
                                os.path.join(dirpath,with_ann_fn), 
                                acs['year'], 
                                acs['span'], 
                                acs['table']]
                            output_row += row
                            output_row += [details.get(h, '') for h in name_details]
                            writer.writerow(output_row)


if __name__ == '__main__':
    assemble_metadata()
    
