# Fetch Census data
#

import os
import sys
import logging
import re
import pdb
import contextlib

import requests  # the fabulous 3rd party package from Kenneth Reitz;
                 # see http://docs.python-requests.org/en/master/
import lxml, lxml.etree


CENSUS_URL = 'http://www2.census.gov'
CENSUS_ACS_URL = "http://www2.census.gov/programs-surveys/acs/summary_file/"
CENSUS_SHELLS_URL = "http://www2.census.gov/programs-surveys/acs/tech_docs/table_shells"
OUTPUT_DIR = "acs_sf_downloads"
HTML_PARSER = lxml.etree.HTMLParser

# areas of potential interest:
# ../tech_docs/table_shells/<year>/*  # Excel files named by table
# http://www2.census.gov/programs-surveys/acs/tech_docs/subject_definitions/  
# set of all subject definition files, PDFs describing (high-level) the
# questions asked
# 

# Directory structure under summary_file
# (http://www2.census.gov/programs-surveys/acs/summary_file/)
# 
# 2005
#   data
#     0UnitedStates
#     Alabama
#       all_al.zip
#       algeo*.zip
# 2006
#   data
#     Alabama
#       al_all_2006.zip
#       g2006al.txt
#     UnitedStates
# 2007
#   data
#     1_year
#       Alabama
#         all_al.zip
#         g20071al.txt
#       UnitedStates
#     3_year
#       Alabama
# 2008/
#   data
#     1_year
#       Alabama
#         all_al.zip
#         g20081al.txt
# 2009
#  data
#    1_year_by_state
#      Alabama.zip
#    *_Summary_FileTemplates.zip
# 2010
#   data
#    1_year_by_state
#      Alabama_All_Geographies.zip
#    *_Summary_FileTemplates.zip
# 2011
#   data
#    1_year_by_state
#        Alabama_All_Geographies.zip
#    *_Summary_FileTemplates.zip
# 
# AVOID getting 'seq_by_state/' directories
# 
# Every page is a bunch 'o divs with links as a header, a table with
# the directory tree (no HTML id, unfortunately) and a bunch o' divs
# with links as a footer. To download all the docs in the tree, just
# follow all the links in the table and download everything with the
# "right" extensions.



SESSION = requests.Session()
ALL_STATES = [
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "DistrictofColumbia",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "NewHampshire",
    "NewJersey",
    "NewMexico",
    "NewYork",
    "NorthCarolina",
    "NorthDakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "PuertoRico",
    "RhodeIsland",
    "SouthCarolina",
    "SouthDakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "WestVirginia",
    "Wisconsin",
    "Wyoming",
    ]


class ACSFetch(object):
    def __init__(self, states='*', tracts_and_block_groups=False, doc_extensions=None):
        if states == '*':
            states = ALL_STATES
        self.states = states
        self.tracts_and_block_groups = tracts_and_block_groups
        if doc_extensions is None:
            doc_extensions = ['.pdf', '.txt', '.xls', '.xlsx', '.csv']
        self.doc_extensions = doc_extensions


    def join_url(self, url_components):
        return '/'.join([c.rstrip('/') for c in url_components])

    def save_file(self, url, outfile, overwrite=False):
        print('    save_file('+url+', '+outfile+')')
        if os.path.exists(outfile):
            if overwrite:
                os.unlink(outfile)
            else:
                return
        with contextlib.closing(SESSION.get(url, stream=True)) as resp:
            tmpfile = outfile+'.part'
            with open(tmpfile, 'wb') as fp:
                for data in resp.iter_content(1024*1024):
                    fp.write(data)
                os.rename(tmpfile, outfile)
    
    
    def fetch_index_links(self, url, in_tbl_only=True):
        index_resp = SESSION.get(url)
        parser = lxml.etree.HTMLParser()
        parser.feed(index_resp.content)
        tree = parser.close()
        search_tree = tree
        if in_tbl_only:
            search_tree = tree.xpath('//table')
            assert(len(search_tree) == 1)
            search_tree = search_tree[0]
        retval = {a.attrib['href']:a.text for a in search_tree.iterdescendants('a') if 'href' in a.attrib}
        for k in retval:
            if retval[k] is not None:
                retval[k] = re.sub('[ \t\n\r]+', ' ', retval[k]).strip()
            else:
                retval[k] = ''
    
        return retval

    def crawl_shells(self, url=CENSUS_SHELLS_URL, output_dir=OUTPUT_DIR):
        if not os.path.exists(output_dir):
            os.mkdir(output_dir, mode=0o755)
        shells_dir = os.path.join(output_dir, 'table_shells')
        if not os.path.exists(shells_dir):
            os.mkdir(shells_dir, mode=0o755)
            
        # get all the ACS links from the main census page
        all_links = self.fetch_index_links(url)
        pat = re.compile('^[0-9]{4}/$')
        links = [l for l in all_links if pat.search(all_links[l])]
        print(links)
        for l in sorted(links):
            dirname = os.path.join(shells_dir, all_links[l]) 
            if not os.path.exists(dirname):
                os.mkdir(dirname, mode=0o755)
            self.recursive_fetch_all(self.join_url([url,all_links[l]]), dirname, ['.xls', '.xlsx', '.csv', '.txt'])
        
    
    def crawl_acs(self, census_url=CENSUS_ACS_URL, output_dir=OUTPUT_DIR):
        """Start at the programs-surveys/acs/summary_file directory and
        handle each included year
        """
        if not os.path.exists(output_dir):
            os.mkdir(output_dir, mode=0o755)
        # get all the ACS links from the main census page
        all_links = self.fetch_index_links(census_url)
        pat = re.compile('^[0-9]{4}/$')
        links = [l for l in all_links if pat.search(all_links[l])]
        print(links)
        for l in sorted(links):
            dirname = os.path.join(output_dir, all_links[l]) 
            if not os.path.exists(dirname):
                os.mkdir(dirname, mode=0o755)
    
            self.crawl_year_dir(self.join_url([census_url, l]), dirname)
    
    
    def crawl_year_dir(self, url, dirname):
        """Handle the top level of a ACS tree, for example
        http://www2.census.gov/programs-surveys/acs/summary_file/2006/ directories
    
        Grab the all the (pdf, txt, csv or .xls) documentation
        Grab "the right" data
        """
        print('crawl_year_dir('+url+', '+dirname+')')
        data_pat = re.compile('data/$')
        doc_pat = re.compile('documentation/$')
        all_links = self.fetch_index_links(url)
        doc_links = [l for l in all_links if doc_pat.search(all_links[l])]
        assert len(doc_links) == 1
        data_links = [l for l in all_links if data_pat.search(all_links[l])]
        assert len(data_links) == 1
    
        # grab all the docs
        doc_dirname = os.path.join(dirname, 'documentation')
        if not os.path.exists(doc_dirname):
            os.mkdir(doc_dirname, mode=0o755)
        self.recursive_fetch_all(self.join_url([url,doc_links[0]]), doc_dirname, self.doc_extensions)

        # fetch all the states
        data_dirname = os.path.join(dirname, 'data')
        if not os.path.exists(data_dirname):
            os.mkdir(data_dirname, mode=0o755)
        self.recursive_fetch_states(self.join_url([url,data_links[0]]), data_dirname)

    

    def recursive_fetch_all(self, url, dirname, extensions):
        print('  recursive_fetch_all('+url+', '+dirname+', '+repr(extensions)+')')
        all_links = self.fetch_index_links(url)
        dir_links = [l for l in all_links if all_links[l].endswith('/')]
        doc_links = []
        for ext in extensions:
            doc_links += [l for l in all_links if all_links[l].endswith(ext)]
        for d in sorted(dir_links):
            subdir = os.path.join(dirname, all_links[d])
            if not os.path.exists(subdir):
                os.mkdir(subdir, mode=0o755)
            self.recursive_fetch_all(self.join_url([url,d]), subdir, extensions)
        for f in sorted(doc_links):
            filename = os.path.join(dirname, all_links[f])
            self.save_file(self.join_url([url,f]), filename)


    def recursive_fetch_states(self, url, dirname):
        print('  recursive_fetch_states('+url+', '+dirname+')')
        all_links = self.fetch_index_links(url)
        dir_links = [l for l in all_links if all_links[l].endswith('/')]
        
        # any state.zip files? If so, grab them.
        poststate_pat = re.compile('(_All_Geographies(_Not_Tracts_Block_Groups)?)?\\.zip')
        if self.tracts_and_block_groups:
            poststate_pat = re.compile('((_All_Geographies(_Not_Tracts_Block_Groups)?)|(_Tracts_Block_Groups_Only))?\\.zip')
            
        state_zips = [s for s in all_links if poststate_pat.sub('', all_links[s]) in self.states]
        for s in sorted(state_zips):
            filename = os.path.join(dirname, all_links[s])
            self.save_file(self.join_url([url,s]), filename)
            
        # Any directories? If so, fetch them.
        state_links = [s for s in all_links if all_links[s].strip('/') in self.states]
        for s in sorted(state_links):
            subdir = os.path.join(dirname, all_links[s])
            if not os.path.exists(subdir):
                os.mkdir(subdir, mode=0o755)
            self.fetch_state(self.join_url([url,s]), subdir, all_links[s].strip('/'))

        # any file templates? If so, save them
        for a in sorted(all_links):
            if re.match('.*File(_)?Templates\\.zip', all_links[a]):
                filename = os.path.join(dirname, all_links[a])
                self.save_file(self.join_url([url,a]), filename)


        # recurse into any directory that looks like N_year or N_year_by_state,
        # but do not recurse into N_year_seq_by_state (or N_year_entire_sf).
        print('    recursive_fetch_states/dir_links: '+repr(dir_links))
        for d in sorted(dir_links):
            if d in state_links:
                continue
            if re.match('^[0-9]_year(_by_state)?/?$', all_links[d]) is not None:
                subdir = os.path.join(dirname, all_links[d])
                if not os.path.exists(subdir):
                    os.mkdir(subdir, mode=0o755)
                self.recursive_fetch_states(self.join_url([url,d]), subdir)
        

    def fetch_state(self, url, dirname, state):
        print('    fetch_state('+url+', '+dirname+', '+state+')')
        pat = re.compile('^((all_[a-z]{2}\\.zip)|([a-z]{2}_all.zip)|(geo.*\\.zip)|(g[0-9]{4}.*\\.txt)|([a-z]{2}geo\\.[0-9]{4}-[0-9]yr))$')
        all_links = self.fetch_index_links(url)
        grab_links = [l for l in all_links if pat.match(all_links[l])]
        for g in sorted(grab_links):
            filename = os.path.join(dirname, all_links[g])
            self.save_file(self.join_url([url,g]), filename)
            

        

    
#     def recurse_acs_data_dir(self, url, dirname)
#         """Handles states, or *_year_by_state directories (2010+
#         Saves *_SummaryFileTemplates.zip
#         """
#         all_links = self.fetch_index_links(url)
#         
#     
#     def handle_summaryfile_dir(self, url, dirname):
#         """Handle a summaryfile dir, like http://www2.census.gov/acs2013_5yr/summaryfile/
#     
#         """
#         all_links = self.fetch_index_links(url)
#     
#         # save the docs
#         doc_pat = re.compile('\\.pdf$')
#         doc_links = [l for l in all_links if doc_pat.search(all_links[l])]
#         for l in doc_links:
#             full_url = self.join_url(url, l)
#             full_filename = os.path.join(dirname, l)
#             save_file(full_url, full_filename)
#     
#         # Now find the data
#         subdir_pat = re.compile('By_State_All_Tables/$')
#         subdir_links = [l for l in all_links if dir_pat.search(all_links[l])]
#         find_data(url, 
    
    
