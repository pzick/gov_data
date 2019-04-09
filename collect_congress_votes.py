""" This file requires the prior installation of xml2json. """

from xml2json import Xml2json
import os

def debug_print(to_print):
    if DEBUG_PRINT is True:
        print(to_print)

# Flag to control either only processing missing files (True), or reprocessing all files (False)
UPDATES_ONLY = True
# Set DEBUG_PRINT to True to get console updates, or False to suppress them
DEBUG_PRINT = True

# Storage directory paths
house_vote_dir = 'house_votes'
senate_vote_dir = 'senate_votes'

# Get a list of files already processed/saved for House votes
try:
    processed_list = os.listdir(house_vote_dir)
except FileNotFoundError:
    os.mkdir(house_vote_dir)
    processed_list = os.listdir(house_vote_dir)

# Set up the base URL name for House roll call vote XML files
rollcall_url_base = 'http://clerk.house.gov/cgi-bin/vote.asp?year=2019&rollnumber='

# Process all House roll call vote pages from 1 to 2000
for vote_number in range(1, 2001):
    if (UPDATES_ONLY is True) and ('roll{}.json'.format(vote_number) in processed_list):
        # If only doing updates and the current roll call number already has a file, skip it
        debug_print('Already processed: roll{}.json'.format(vote_number))
        continue
    # Create the URL for the roll call page to process
    url = '{}{}'.format(rollcall_url_base, vote_number)
    debug_print(f'Trying {url}')

    # Pass the URL for the roll call xml file to the Xml2json wrapper class and get the results back
    out = Xml2json().convertFromXmlUrl(url)
    if out is None:
        # If there was a URL error detected, stop the processing loop for House votes
        debug_print('File not found')
        break
    if not ('rollcall-vote' in out.keys()):
        # congress.gov generates an html page if you go beyond the actual vote pages
        # Detect an error page to break the processing loop
        debug_print('File not found')
        break
    filename = '{}/roll{}.json'.format(house_vote_dir, vote_number)
    Xml2json().saveToJsonFile(out, filename)

# Get a list of files already processed/saved for Senate votes
try:
    processed_list = os.listdir(senate_vote_dir)
except FileNotFoundError:
    os.mkdir(senate_vote_dir)
    processed_list = os.listdir(senate_vote_dir)
# Set up the base URL name for Senate roll call vote XML files
base_url = 'https://www.senate.gov/legislative/LIS/roll_call_votes/vote1161/vote_116_1_' # 00000.xml

# Process all Senate roll call vote pages from 1 to 2000
for vote_page in range(1, 2001):
    # Format the string version of the current roll call number to have leading zeroes enough to have 5 digits
    vote_number_formatted = str(vote_page).zfill(5)
    out_filename = f'vote{vote_number_formatted}.json'
    if (UPDATES_ONLY is True) and (out_filename in processed_list):
        # If only doing updates and the current roll call number already has a file, skip it
        debug_print(f'Already processed: {out_filename}')
        continue

    # Create the URL for the roll call page to process
    url = '{}{}.xml'.format(base_url, vote_number_formatted)
    debug_print(f'Trying {url}')

    # Pass the URL for the roll call xml file to the Xml2json wrapper class and get the results back
    out = Xml2json().convertFromXmlUrl(url)
    if out is None:
        # If there was a URL error detected, stop the processing loop for House votes
        debug_print('File not found')
        break
    elif not ('roll_call_vote' in out.keys()):
        # For the Senate, the error detection above works when no more pages are available, but if that
        # changes to have a generated file, this guard would detect the end of processing
        debug_print('File not found')
        break
    filename = '{}/{}'.format(senate_vote_dir, out_filename)
    Xml2json().saveToJsonFile(out, filename)
