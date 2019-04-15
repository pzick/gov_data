""" This file requires the prior installation of xml2json. """

from xml2json import Xml2json
import os
from time import sleep


class CollectCongressVotes:
    def __init__(self, year=2019, updates_only=True, dbg_print=False):
        # Flag to control either only processing missing files (True), or reprocessing all files (False)
        self.UPDATES_ONLY = updates_only
        # Set DEBUG_PRINT to True to get console updates, or False to suppress them
        self.DEBUG_PRINT = dbg_print

        self.year = year
        self.Congress_start_year = 1787
        self.Sessions_per_Congress = 2

        # Subtract the start of Congress year 1787 from the year of interest, divide by two for the Congress number
        self.congress = (self.year - self.Congress_start_year) / self.Sessions_per_Congress
        # If the vote year calculated ends with .5, it is the second session, otherwise it is the first session
        if self.congress > int(self.congress):
            self.session = 2
            self.congress = int(self.congress)
        else:
            self.session = 1
            self.congress = int(self.congress)

        # Storage directory paths
        self.house_vote_dir = 'house_votes_{}'.format(self.year)
        self.senate_vote_dir = 'senate_votes_{}'.format(self.year)

        # Get a list of files already processed/saved for House votes
        try:
            self.processed_list = os.listdir(self.house_vote_dir)
        except FileNotFoundError:
            os.mkdir(self.house_vote_dir)
            self.processed_list = os.listdir(self.house_vote_dir)

        # Set up the base URL name for House roll call vote XML files
        self.rollcall_url_base = 'http://clerk.house.gov/evs/{}/roll'.format(self.year)
        # Get a list of files already processed/saved for Senate votes
        try:
            self.senate_processed_list = os.listdir(self.senate_vote_dir)
        except FileNotFoundError:
            os.mkdir(self.senate_vote_dir)
            self.senate_processed_list = os.listdir(self.senate_vote_dir)
        # Set up the base URL name for Senate roll call vote XML files
        # (append vote number and .xml with zero pad of 5 digits)
        self.senate_base_url = 'https://www.senate.gov/legislative/LIS/'\
                               'roll_call_votes/vote{}{}/vote_{}_{}_'.format(self.congress, self.session,
                                                                             self.congress, self.session)

    def collect_house_votes(self):
        # Process all House roll call vote pages from 1 to 2000
        for vote_number in range(1, 2001):
            if (self.UPDATES_ONLY is True) and ('roll{}.json'.format(vote_number) in self.processed_list):
                # If only doing updates and the current roll call number already has a file, skip it
                self.debug_print('Already collected: roll{}.json'.format(vote_number))
                continue
            # Create the URL for the roll call page to process
            url = '{}{}.xml'.format(self.rollcall_url_base, str(vote_number).zfill(3))
            self.debug_print(f'Trying {url}')

            # Pass the URL for the roll call xml file to the Xml2json wrapper class and get the results back
            out = Xml2json().convertFromXmlUrl(url)
            if out is None:
                # If there was a URL error detected, stop the processing loop for House votes
                self.debug_print('File not found')
                break
            if not ('rollcall-vote' in out.keys()):
                # congress.gov generates an html page if you go beyond the actual vote pages
                # Detect an error page to break the processing loop
                self.debug_print('File not found')
                break
            filename = '{}/roll{}.json'.format(self.house_vote_dir, vote_number)
            Xml2json().saveToJsonFile(out, filename)

    def collect_senate_votes(self):
        # Process all Senate roll call vote pages from 1 to 2000
        for vote_page in range(1, 2001):
            # Format the string version of the current roll call number to have leading zeroes enough to have 5 digits
            vote_number_formatted = str(vote_page).zfill(5)
            out_filename = f'vote{vote_number_formatted}.json'
            if (self.UPDATES_ONLY is True) and (out_filename in self.senate_processed_list):
                # If only doing updates and the current roll call number already has a file, skip it
                self.debug_print(f'Already collected: {out_filename}')
                continue

            # Create the URL for the roll call page to process
            url = '{}{}.xml'.format(self.senate_base_url, vote_number_formatted)
            self.debug_print(f'Trying {url}')

            # Pass the URL for the roll call xml file to the Xml2json wrapper class and get the results back
            out = Xml2json().convertFromXmlUrl(url)
            if out is None:
                # If there was a URL error detected, stop the processing loop for House votes
                self.debug_print('File not found')
                break
            elif not ('roll_call_vote' in out.keys()):
                # For the Senate, the error detection above works when no more pages are available, but if that
                # changes to have a generated file, this guard would detect the end of processing
                self.debug_print('File not found')
                break
            filename = '{}/{}'.format(self.senate_vote_dir, out_filename)
            Xml2json().saveToJsonFile(out, filename)
            # Delay between senate.gov access attempts, one second
            sleep(2)

    def collect_votes(self):
        self.collect_house_votes()
        self.collect_senate_votes()

    def debug_print(self, to_print):
        if self.DEBUG_PRINT is True:
            print(to_print)


if __name__ == '__main__':
    collect = CollectCongressVotes(2016, True, True)
    collect.collect_votes()
