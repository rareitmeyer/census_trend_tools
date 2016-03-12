# Search through assembled metadata and search for
# matching columns based on regex pattern(s).

# Copyright R. A. Reitmeyer
# Released under the GNU Public License, version 2, or later.


# Documentation note: parens are treated as LITERAL parens,
# because it's too easy to have a cut-and-paste of text with
# a real paren, like "median income (dollars)", and it's unkind
# to make a user escape all those.  So use escaped parens if
# you want regex behavior.

import os
import sys
import re
import time
import csv
import logging
import argparse
import pprint
import pdb

NOW = time.time()

if not os.path.exists("logs"):
    os.mkdir("logs")

logging.basicConfig(
    filename=os.path.join('logs',__file__+time.strftime('.%Y%m%d_%H%M%S.log', time.localtime(NOW))),
    format='%(asctime)|%(levelno)|%(levelname)|%(filename)|%(lineno)|%(message)',
    level=logging.DEBUG
    )


def load_metadata(metadata_filename='all_metadata.csv', build_cmd='python3 assemble_metadata.py'):
    if not os.path.exists(metadata_filename):
        assert(os.system(build_cmd) == 0)
    with open(metadata_filename, 'r', newline='', encoding='utf-8') as fp:
        reader = csv.DictReader(fp)
        return [ rec for rec in reader ]
        

def flip_quotes(pattern):
    retval = ''
    backslashes = 0
    for i in range(len(pattern)):
        if pattern[i] == '\\':
            backslashes += 1
        elif pattern[i] in ['(',')']:
            if backslashes % 2 == 0:
                retval += backslashes*'\\' + '\\' + pattern[i]
            else:
                retval += (backslashes-1)*'\\' + pattern[i]
            backslashes = 0
        else:
            if backslashes > 0:
                retval += backslashes*'\\'
                backslashes = 0
            retval += pattern[i]
    return retval


def expand_pattern(pattern, template='{year}', expanded='(?P<year>[0-9]{4})'):
    """Expands a pattern, intended for use before the regex search
    begins. EG, let a user make a pattern like '({year} dollars)'
    without needing to understand how ot make a pattern for year.

    >>> expand_pattern("hello, world", '{year}', 'YEARSTUFF')
    "hello, world"
    >>> expand_pattern("({year} dollars)", '{year}', 'YEARSTUFF')
    "(YEARSTUFF dollars)"
    """
    i = pattern.find(template)
    if i >=0:
        pattern = pattern[:i] + expanded + pattern[i+len(template):]
    return pattern


def expand_all_patterns(pattern):
    """Expand all the pattern rules.
    Just one for now.
    """
    return expand_pattern(pattern, '{year}', '(?P<year>[0-9]{4})')


def abstract_year(value):
    return re.sub('(?P<year>[0-9]{4})', '{year}', value)


def pattern_scan(md, rules):
    """Search for cols matching the given rules (rules AND'd together).
    Each rule is a small dict with keys for colname, pattern, and
    (optionally) flags. If flags is not given, re.IGNORECASE is assumed.
    """
    retval = []
    for r in rules:
        r['regex'] = re.compile(r['pattern'], r.get('flags', re.IGNORECASE))
    for rec in md:
        use = True
        for r in rules:
            if r['regex'].search(rec[r['colname']]) is None:
                use = False
                break
        if use:
            rec['LONGCOLNAME_ar'] = abstract_year(rec['LONGCOLNAME'])
            rec['NAME_ar'] = abstract_year(rec['NAME'])

            retval.append(rec)
    return retval


def parse_args(args=None):
    parser = argparse.ArgumentParser(description='Search Census columns.')
    parser.add_argument('-e', dest='est_only', action='store_true', help='Just search estimates')
    parser.add_argument('-r', dest='insensitive_rules', nargs=2, action='append', help='define case-insensitive rule as a COLNAME PATTERN pair')
    parser.add_argument('-R', dest='sensitive_rules', nargs=2, action='append', help='define case-sensitive rule as a COLNAME PATTERN pair')
    parser.add_argument('-y', dest="years_only", action="store_true", help="Just report pattern and matching years")
    parser.add_argument('-c', dest="output_cols", nargs="*", help="list of output columns")
    return parser.parse_args(args)
                        

def output(header, recs):
    writer = csv.writer(sys.stdout)
    writer.writerow(header)
    for r in recs:
        writer.writerow([r[k] for k in header])


def main():
    args = parse_args()
    rules = []
    if args.insensitive_rules is not None:
        for r in args.insensitive_rules:
            rules.append({'colname': r[0], 'pattern': expand_all_patterns(flip_quotes(r[1])), 'flags': re.IGNORECASE})
    if args.sensitive_rules is not None:
        for r in args.sensitive_rules:
            rules.append({'colname': r[0], 'pattern': expand_all_patterns(flip_quotes(r[1])), 'flags': 0})
    if args.est_only is not None and args.est_only:
        rules.append({'colname': 'EST_OR_MARGIN', 'pattern': '^ESTIMATE$'})
        pass
    # substitute year pattern
    md = load_metadata('all_metadata.csv', 'python3 assemble_metadata.py')
    cols = pattern_scan(md, rules)
    if args.years_only is not None and args.years_only:
        longnames = {}
        for c in cols:
            rec = {}
            if c['LONGCOLNAME_ar'] in longnames:
                prior = longnames[c['LONGCOLNAME_ar']]
                rec['years'] = set([c['ACS_YEAR']]) | prior['years']
                rec['tables'] = set([c['TABLE']]) | prior['tables']
                rec['shortcolnames'] = set([c['SHORTCOLNAME']]) | prior['shortcolnames']
            else:
                rec['years'] = set([c['ACS_YEAR']])
                rec['tables'] = set([c['TABLE']])
                rec['shortcolnames'] = set([c['SHORTCOLNAME']])
                                                                            
                                                                        
            longnames[c['LONGCOLNAME_ar']] = rec
        # order by count and summarize years
        longnames_order = sorted([(len(longnames[k]['years']),k) for k in longnames], reverse=True)
        header = ['count', 'LONGCOLNAME_ar', 'tables', 'shortcolnames', 'years']
        summary = [{'count':c, 
                    'LONGCOLNAME_ar':k, 
                    'tables': ' '.join(sorted(longnames[k]['tables'])), 
                    'shortcolnames': ' '.join(sorted(longnames[k]['shortcolnames'])), 
                    'years':' '.join(sorted(longnames[k]['years']))} 
                   for c,k in longnames_order]

        output(header, summary)
    else:
        header = ['LONGCOLNAME_ar', 'ACS_YEAR', 'ACS_SPAN', 'EST_OR_MARGIN', 'NAME_ar', 'ROLLUP1', 'ROLLUP2', 'SHORTCOLNAME', 'TABLE', 'FILENAME', 'LONGCOLNAME', 'NAME']
        if args.output_cols is not None:
            for c in args.output_cols:
                assert c in md[0].keys()
            header = args.output_cols
        output(header, cols)
        



if __name__ == '__main__':
    main()



