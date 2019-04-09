import requests
import bs4
from bs4 import BeautifulSoup
import json
from time import sleep

class Xml2json:
    """ A class wrapper to take a url to an xml file, convert it to a JSON-style format, and optionally write
        the file to disk. This class depends on the prior installation of requests, bs4 (Beautiful Soup),
        and json. """
    def _processChild(self, child):
        """ This function is called recursively to unfold all layers of the XML tree into
            dictionaries and lists. """
        dictionary = {}
        child_list = []
        for item in child:
            # Skip empty lines of the XML file
            if item == '\n':
                continue
            # If there are attributes for the item, add them to the dictionary,
            # and preserve any text between the tag start and stop
            if len(item.attrs) > 0:
                dictionary[item.name] = {}
                dictionary[item.name]['attributes'] = item.attrs
                dictionary[item.name]['text'] = item.string
            elif not (item.string is None):
                # If the item is a leaf node, add the text content of the item to the dictionary
                dictionary[item.name] = item.string
            else:
                # Otherwise, process the next layer of children from the current item
                result = self._processChild(item)
                # Detect if there is a list of children at the same level rather than independent children
                if (item.name in dictionary.keys()) and (len(child_list) == 0):
                    # If there is already a dictionary entry for a child with the same name and a list
                    # has not already been started, move that entry into a list and remove it from the
                    # dictionary
                    child_list = [{item.name: dictionary[item.name]}]
                    dictionary.pop(item.name, None)
                if len(child_list) > 0:
                    # If a list of child elements with the same name has been started, append the latest
                    # item processed to the list
                    child_list.append({item.name: result})
                else:
                    # If this is a new child name, just add it to the dictionary
                    dictionary[item.name] = result

        if len(child_list) > 0:
            # If this item has a list of children rather than a dictionary, return the list
            dictionary = child_list
        elif len(dictionary) == 0:
            # If there is no list and nothing was added to the dictionary, it was an empty node, return
            # a null string of ''
            dictionary = ''
        return dictionary

    def convertFromXmlUrl(self, url):
        """ This function checks that there was no error in accessing the target url, then starts from
            the root tag to walk the XML tree from the url. Line returns and child items with no names
            are skipped. If there was a url read error, None is returned, otherwise a JSON-style
            dictionary of dictionaries and lists form of the XML file is returned."""
        r = requests.get(url)
        # Delay in attempt to resolve Senate vote scraping issues where data does not come through right
        sleep(0.5)
        if r.status_code != 200:
            # If the return code was not 200, something is not right, return a None object
            print('Status: {}'.format(r.status_code))
            return None
        # Use Beautiful Soup 4 to process the XML file into tags in a structure to parse and repackage
        soup = BeautifulSoup(r.text, 'xml')
        # Set the return value (store) to an empty dictionary
        store = {}
        for child in soup:
            # Starting at the root of the parsed tags structure (soup)
            if (child == '\n') or (child.name is None) or (isinstance(child, bs4.element.Comment)):
                # If the line to process is empty (just a return character) or the tag has no name
                # or the child item is a Comment data type, skip it
                continue
            # Process the current child node through the recursive function call to processChild,
            # and store the returned dictionary (or list) in the return dictionary
            store[child.name] = self._processChild(child)
        return store

    def saveToJsonFile(self, outJson, filename):
        """ Save the JSON-style data structure to a file. Generally, the 'store' returned by the
            convertFromXmlUrl function will be passed to this function as the outJson input, but
            any JSON-style data structure could be passed in here. """
        with open(filename, 'w') as f:
            # Use indent=1 to balance readability of the output file with the extra space used up by
            # space characters
            f.write(json.dumps(outJson, indent=1))
