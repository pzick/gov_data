# gov_data
This project collects the voting records of the US Congress (both chambers) and creates graphs showing the vote results overall and by party.

collect_congress_votes.py cycles through the available vote record pages on congress.gov, converts the XML files found to a JSON format, and saves the results to a local subdirectory. The process is repeated for the senate.gov vote record pages available.

process_congress_votes.py reads the saved JSON files from the House and Senate subdirectories, creates PNG images of nested pie charts showing the vote records in graph form, and creates an HTML file to display the graphs ordered from most recent to earliest vote for the current congress.

Both files have an UPDATES_ONLY flag which can be left True to only process vote record pages which are newer than the most recent processing cycle, or missing. Or the UPDATES_ONLY flag can be set False to force reprocessing of all vote pages for the collect process or all images for the process votes procedure.

Python Dependencies: json, requests, bs4 (Beautiful Soup), numpy, matplotlib

Notes: Although the file reads from congress.gov seem very reliable, the senate.gov access seems less so. It may be necessary to try running the collect_congress_vote.py script a couple of times with UPDATES_ONLY set True to get through whatever timing issue is happening and get all the Senate votes collected.

This initial commit is intended as a proof of concept only. Further development is needed to properly test and clean the code.
