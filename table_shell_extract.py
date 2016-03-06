import os
import sys
import csv
import re


import openpyxl 

def extract(writer, infilepath, write_header=True):
    header = ['year', 'variable.code', 'table.number', 'table.name', 'population', 'desc', 'indent', 'full_desc', 'filepath']
    if write_header:
        writer.writerow(header)
    m = re.search('table_shells/(?P<year>[0-9]{4})/', infilepath)
    year = m.group('year')
    workbook = openpyxl.load_workbook(infilepath)
    worksheet = workbook.active # just one sheet
    indents_stack = []
    indents_desc = {}
    table_name = ''
    population = ''
    for rownum, row in enumerate(worksheet.iter_rows()):
        if rownum == 0:
            continue # header
        if rownum == 1:
            table_name = cell_c.value
            continue # table name
        if rownum == 2:
            population = cell_c.value
            continue # population
        assert(len(row) == 3)
        (cell_a, cell_b, cell_c) = row
        indent = cell_c.alignment.indent

        # would love to do indents_stack.find(indent) but that's not available.
        # so do it the tedious way.
        idx = -1
        for i in range(len(indents_stack)):
            if indents_stack[i] == indent:
                idx = i
                break

        if idx >= 0:
            for j in range(idx, len(indents_stack)):
                del indents_desc[j]
            del indents_stack[idx:]
        assert(indents_stack == [] or indents_stack[-1] < indent)
        indents_stack.append(indent)
        idx
        desc = cell_c.value         #.rstrip(': ').lstrip(' ')
        indents_desc[indent] = desc
        full_desc = '; '.join([indents_desc[i] for i in indents_stack])
        variable_code = '{table_id}_{line_num:03d}'.format(table_id=table_id, line_num=int(cell_b.value))
        
        record = {
            'year': year,
            'variable.code': variable_code,
            'table.number': table_id,
            'table.name': table_name,
            'population': population,
            'desc': desc,
            'indent': indent,
            'full_desc': full_desc,
            'filepath': infilepath,
            }
        writer.writerow([record[k] for k in header])


