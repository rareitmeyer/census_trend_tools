= One Sentence Summary = 

This is a suite of tools to work with US Census bulk data across
multiple years, for trending purposes.


= Motivation =

Column names (long and short) are consistent between locations and
geographies within a year, but can change from year to year.
It's not trivial to find the data of interest.

For example, consider the size of the civilian labor force.

Other packages (for example, the "acs" package in R) will let you search
through all of the long column names to find that estimate. In 
2014, that estimate is in table S0102 and has the (long) column name
"Total; Estimate; EMPLOYMENT STATUS - Population 16 years and over - In labor force - Civilian labor force"

But in 2010-2012, it was called "Total; Estimate; EMPLOYMENT STATUS - In labor force - Civilian labor force"

Using the "short" column names, the estimate has appeared as several columns:

2005:      HC01_EST_VC80
2006-2009: HC01_EST_VC81
2010-2012: HC01_EST_VC107
2013-2014: HC01_EST_VC95

The initial tools in this suite are intended to help spot where data
lives across years, not just within a single year.


= Use Overview =

Download census data for the geographies and years of interest from 
the American Fact Finder, as a set of zip files. 

Use the burst.py script to extract those files into a directory
hierarchy by type of geography (place vs non-place) and year.

Use the assemble_metadata.py script to build up a single CSV
file for all the metadata.

Then use the colsearch.py script to search for columns of interest.

Create a spreadsheet of those columns, organized by year.
