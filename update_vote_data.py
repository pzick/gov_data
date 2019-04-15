from collect_congress_votes import CollectCongressVotes
from process_congress_votes import ProcessCongressVotes

year = 2019
updates_only = True
debug_print = True

collect = CollectCongressVotes(year, updates_only, debug_print)
collect.collect_votes()
process = ProcessCongressVotes(year, updates_only)
process.process_votes()
