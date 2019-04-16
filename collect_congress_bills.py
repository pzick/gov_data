import os
from datetime import datetime as dt
import requests
import re
import json


class CollectCongressBills:
    def __init__(self, year, updates_only=True, dbg_print=False):
        self.year = year
        self.UPDATES_ONLY = updates_only
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

        # Storage directory path
        self.congress_bills_dir = 'congress_bills_{}'.format(self.year)
        try:
            self.collected_congress_bills = os.listdir(self.congress_bills_dir)
        except FileNotFoundError:
            os.mkdir(self.congress_bills_dir)
            self.collected_congress_bills = os.listdir(self.congress_bills_dir)

        self.bill_type = {'house_bills': {
                                'url_base': 'https://www.congress.gov/bill/{}th-congress/house-bill/{}',
                                'filename_base': 'House_bills_',
                                'page_title': 'House Bills'},
                          'house_resolutions': {
                              'url_base': 'https://www.congress.gov/bill/{}th-congress/house-resolution/{}',
                              'filename_base': 'House_resolutions_',
                              'page_title': 'House Resolutions'},
                          'house_joint_resolutions': {
                              'url_base': 'https://www.congress.gov/bill/{}th-congress/house-joint-resolution/{}',
                              'filename_base': 'House_joint_resolutions_',
                              'page_title': 'House Joint Resolutions'},
                          'senate_bills': {
                              'url_base': 'https://www.congress.gov/bill/{}th-congress/senate-bill/{}',
                              'filename_base': 'Senate_bills_',
                              'page_title': 'Senate Bills'},
                          'senate_resolutions': {
                              'url_base': 'https://www.congress.gov/bill/{}th-congress/senate-resolution/{}',
                              'filename_base': 'Senate_resolutions_',
                              'page_title': 'Senate Resolutions'},
                          'nominations': {
                              'url_base': 'https://www.congress.gov/nomination/{}th-congress/{}',
                              'filename_base': 'Nominations_',
                              'page_title': 'Nominations'}
                          }

    def collect_bills(self, bill_type, new_only=False, limit=None):
        if new_only is False or '{}{}.json'.format(self.bill_type[bill_type]['filename_base'], self.year)\
                not in self.collected_congress_bills:
            collected_bills = {'bill_data': {'last_bill': 0, 'bill': []}}
            start_number = 1
        else:
            with open('{}/{}{}.json'.format(self.congress_bills_dir,
                                            self.bill_type[bill_type]['filename_base'],
                                            self.year), 'r') as f:
                collected_bills = json.load(f)
            start_number = collected_bills['bill_data']['last_bill'] + 1

        # Collect the bills from congress.gov
        if limit is None:
            max_bill_number = 100000
        else:
            max_bill_number = limit
        for number in range(start_number, max_bill_number):
            url = self.bill_type[bill_type]['url_base'].format(self.congress, number)
            self.debug_print('Trying: {}'.format(url))
            r = requests.get(url)
            if r.status_code == 200:
                title_start = r.text.find('<title>') + len('<title>')
                title_end = r.text.find('</title>')
                tracker_start = r.text.find('<p class="hide_fromsighted">')
                bill = {'title': r.text[title_start:title_end],
                        'url': url + '/text',
                        'number': number,
                        'cosponsors': url + '/cosponsors'}
                if tracker_start >= 0:
                    tracker_start += len('<p class="hide_fromsighted">')
                    tracker_end = r.text[tracker_start:].find('</p>')
                    bill['status'] = r.text[tracker_start:tracker_start+tracker_end]
                    # Check for Sponsor
                    sponsor_start = r.text.find('Sponsor:')
                    if sponsor_start >= 0:
                        sponsor_at = re.search(r'<td><a\W.*>(.*?)</a>(.*?)</td>', r.text[sponsor_start:])
                        if sponsor_at is not None:
                            sponsor = sponsor_at.group(1)
                            sponsor_intro = sponsor_at.group(2)
                            bill['sponsor'] = sponsor
                            bill['introduced'] = sponsor_intro
                            if sponsor.find('[R-') >= 0:
                                party = 'Republican'
                            elif sponsor.find('[D-') >= 0:
                                party = 'Democratic'
                            else:
                                party = 'Independent'
                            bill['party'] = party
                    # Check for Committee
                    committee_start = r.text.find('Committees:')
                    if committee_start >= 0:
                        committees = re.search('<td>(.*?)</td>', r.text[committee_start:])
                        if committees is not None:
                            bill['committees'] = committees.group(1)
                    # Check for Committee Report
                    committee_reports_start = r.text.find('Committee Reports:')
                    if committee_reports_start >= 0:
                        committee_reports = re.search(r'<td><a\W.*?href="(.*?)">(.*?)</a></td>',
                                                      r.text[committee_reports_start:])
                        if committee_reports is not None:
                            bill['committee_reports'] = committee_reports.group(2)
                            bill['committee_reports_url'] = committee_reports.group(1)
                    # Check for Latest Action
                    action_start = r.text.find('Latest Action:')
                    if action_start >= 0:
                        action = re.search(r'<td>(.*?)\(<a\W.*?href="(.*?)">(.*?)</a>.*</td>', r.text[action_start:])
                        if action is not None:
                            bill['latest_action'] = action.group(1)
                            bill['all_actions_url'] = action.group(2)
                    policy_start = r.text.find('Policy Area:<')
                    if policy_start >= 0:
                        policy = re.search(r'<li>(.*?)</li>', r.text[policy_start:])
                        if policy is not None:
                            bill['policy_area'] = policy.group(1)
                            subjects = re.search(r'<li><a\W.*?href="(.*?)">', r.text[policy_start:])
                            if subjects is not None:
                                bill['subjects'] = 'https://www.congress.gov' + subjects.group(1)
                else:
                    bill['reserved'] = True
                collected_bills['bill_data']['last_bill'] = number
                collected_bills['bill_data']['bill'].append(bill)
            else:
                print('Not found')
                break
        self.update_html(bill_type, collected_bills)

    def collect_nominations(self, bill_type, new_only=False, limit=None):
        if new_only is False or '{}{}.json'.format(self.bill_type[bill_type]['filename_base'], self.year)\
                not in self.collected_congress_bills:
            collected_bills = {'bill_data': {'last_bill': 0, 'bill': []}}
            start_number = 1
        else:
            with open('{}/{}{}.json'.format(self.congress_bills_dir,
                                            self.bill_type[bill_type]['filename_base'],
                                            self.year), 'r') as f:
                collected_bills = json.load(f)
            start_number = collected_bills['bill_data']['last_bill'] + 1

        # Collect the bills from congress.gov
        if limit is None:
            max_bill_number = 100000
        else:
            max_bill_number = limit
        for number in range(start_number, max_bill_number):
            url = self.bill_type[bill_type]['url_base'].format(self.congress, number)
            self.debug_print('Trying: {}'.format(url))
            r = requests.get(url)
            if r.status_code == 200:
                title_start = r.text.find('<title>') + len('<title>')
                title_end = r.text.find('</title>')
                tracker_start = r.text.find('<p class="hide_fromsighted">')
                bill = {'title': r.text[title_start:title_end],
                        'url': url,
                        'number': number}
                # Find Description, Latest Action, Date Received from President, Committee, All Actions
                description_start = r.text.find('>Description<')
                if description_start >= 0:
                    description_start += len('>Description<')
                    description = re.search('<li>(.*?)</li>', r.text[description_start:])
                    if description is not None:
                        bill['description'] = description.group(1)
                committee_start = r.text.find('>Committee<')
                if committee_start >= 0:
                    committee_start += len('>Committee<')
                    committee = re.search('<li>(.*?)</li>', r.text[committee_start:])
                    if committee is not None:
                        bill['committees'] = committee.group(1)
                organization_start = r.text.find('>Organization</h2>')
                if organization_start >= 0:
                    organization_start += len('>Committee<')
                    organization = re.search('<li>(.*?)</li>', r.text[organization_start:])
                    if organization is not None:
                        bill['organization'] = organization.group(1)
                latest_action_start = r.text.find('>Latest Action<')
                if latest_action_start >= 0:
                    latest_action_start += len('>Latest Action<')
                    latest_action = re.search('<li>(.*?)</li>', r.text[latest_action_start:])
                    if latest_action is not None:
                        bill['latest_action'] = latest_action.group(1)
                date_received_start = r.text.find('>Date Received from President<')
                if date_received_start >= 0:
                    date_received_start += len('>Date Received from President<')
                    date_received = re.search('<li>(.*?)</li>', r.text[date_received_start:])
                    if date_received is not None:
                        bill['date_received'] = date_received.group(1)
                collected_bills['bill_data']['last_bill'] = number
                collected_bills['bill_data']['bill'].append(bill)
            else:
                print('Not found')
                break
        self.update_html(bill_type, collected_bills)

    def update_html(self, bill_type, collected_bills):
        # Create/update the HTML page
        html = '<html>\n<head>\n<title>{} {}</title>'.format(self.bill_type[bill_type]['page_title'], self.year)
        html += '\n<link rel="stylesheet" href="bill_style.css">\n</head>\n'
        html += '<h1>{} {}</h1>\n'.format(self.bill_type[bill_type]['page_title'], self.year)
        html += '<body>\n<h2>Last updated {}</h2><br>\n'.format(dt.now().strftime('%B %d, %Y'))

        for bill in collected_bills['bill_data']['bill']:
            html += '<br><a href="{}"><font class="bill_title"><b>{}</b></font></a>\n'\
                .format(bill['url'], bill['title'])
            if 'status' in bill.keys():
                if bill['status'].find('Passed') >= 0:
                    html += '<li><font class="passed"><b>{}</b></font></li>\n'.format(bill['status'])
                elif bill['status'].find('Became Law') >= 0:
                    html += '<li><font class="became_law"><b>{}</b></font></li>\n'.format(bill['status'])
                elif bill['status'].find('Agreed to') >= 0:
                    html += '<li><font class="agreed"><b>{}</b></font></li>\n'.format(bill['status'])
                else:
                    html += '<li><b>{}</b></li>\n'.format(bill['status'])
            if 'sponsor' in bill.keys():
                html += '<li><font class="{}">{}</font></li>\n'.format(bill['party'], bill['sponsor'])
                html += '<li>{}</li>\n'.format(bill['introduced'])
            if 'description' in bill.keys():
                html += '<li>{}</li>\n'.format(bill['description'])
            if 'committees' in bill.keys():
                html += '<li>Committee(s): {}</li>\n'.format(bill['committees']
                                                             .replace('href="', 'href="https://www.congress.gov/'))
            if 'committee_reports' in bill.keys():
                html += '<li><a href="https://www.congress.gov/{}">{}</a></li>\n'\
                    .format(bill['committee_reports_url'], bill['committee_reports'])
            if 'date_received' in bill.keys():
                html += '<li>Date Received from President: {}</li>\n'.format(bill['date_received'])
            if 'organization' in bill.keys():
                html += '<li>Organization: {}</li>\n'.format(bill['organization'])
            if 'latest_action' in bill.keys():
                if bill['latest_action'].find('Confirmed by') >= 0:
                    html += '<li><font class="confirmed">{}</font></li>\n'\
                        .format(bill['latest_action'].replace('href="', 'href="https://www.congress.gov/'))
                else:
                    html += '<li>{}</li>\n'\
                        .format(bill['latest_action'].replace('href="', 'href="https://www.congress.gov/'))
            if 'all_actions_url' in bill.keys():
                html += '<li><a href="https://www.congress.gov/{}">All actions</a></li>\n'\
                    .format(bill['all_actions_url'])
            if 'cosponsors' in bill.keys():
                html += '<li><a href="{}">Cosponsors</a></li>\n'.format(bill['cosponsors'])
            if 'policy_area' in bill.keys():
                if 'subjects' in bill.keys():
                    html += '<li>Policy Area: <a href="{}">{}</a></li>\n'.format(bill['subjects'], bill['policy_area'])
                else:
                    html += '<li>Policy Area: {}</li>\n'.format(bill['policy_area'])
            if 'reserved' in bill.keys():
                html += '<li>Reserved</li>\n'
            html += '<br>\n'

        html += '</body>\n</html>'
        # Save JSON file
        with open('{}/{}{}.json'.format(self.congress_bills_dir,
                                        self.bill_type[bill_type]['filename_base'],
                                        self.year), 'w') as f:
            f.write(json.dumps(collected_bills, indent=1))
        # Save HTML file
        with open('{}{}.html'.format(self.bill_type[bill_type]['filename_base'], self.year), 'wt') as f:
            f.write(html)


    def debug_print(self, to_print):
        if self.DEBUG_PRINT is True:
            print(to_print)


if __name__ == '__main__':
    collect = CollectCongressBills(2019, True, True)
    collect.collect_bills('house_bills', True, None)
    collect.collect_bills('senate_bills', True, None)
    collect.collect_bills('house_resolutions', True, None)
    collect.collect_bills('senate_resolutions', True, None)
    collect.collect_nominations('nominations', True, None)
