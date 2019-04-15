import os
import json
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime as dt


def wrap_text(text, max_characters):
    if len(text) > max_characters:
        words = text.split(' ')
        composite = ''
        new_len = 0
        for word in words:
            if new_len + len(word) + 1 < max_characters:
                composite += ' ' + word
                new_len += len(word) + 1
            else:
                composite += '\n' + word
                new_len = len(word)
        text = composite
    return text


class ProcessCongressVotes:
    def __init__(self, year=2019, updates_only=True):
        self.year = year
        # Flag to control either only processing missing files (True), or reprocessing all files (False)
        self.UPDATES_ONLY = updates_only
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

        # Set up the base URL name for House roll call vote XML files
        self.rollcall_url_base = 'http://clerk.house.gov/evs/{}/roll'.format(self.year)
        # Set up the base URL name for Senate roll call vote XML files (append vote number with zero pad of 5 digits)
        self.base_url = 'https://www.senate.gov/legislative/LIS/roll_call_lists/' \
                        'roll_call_vote_cfm.cfm?congress={}&session={}&vote='.format(self.congress, self.session)

        # Storage directory paths
        self.house_vote_dir = 'house_votes_{}'.format(self.year)
        self.senate_vote_dir = 'senate_votes_{}'.format(self.year)
        # Images directory
        self.images_dir = 'images_{}'.format(self.year)

        # Create the images directory if it is not found
        try:
            os.listdir(self.images_dir)
        except FileNotFoundError:
            os.mkdir(self.images_dir)
        # Get list of existing image files
        self.image_files = os.listdir(self.images_dir)
        self.image_files = [f for f in self.image_files if f.endswith('.png')]

        # Create the House votes directory if it is not found
        try:
            os.listdir(self.house_vote_dir)
        except FileNotFoundError:
            os.mkdir(self.house_vote_dir)
        # Get House votes from files
        house_votes_files = os.listdir(self.house_vote_dir)
        house_votes_files = [f for f in house_votes_files if f.startswith('roll') and f.endswith('.json')]

        # Create the Senate votes directory if it is not found
        try:
            os.listdir(self.senate_vote_dir)
        except FileNotFoundError:
            os.mkdir(self.senate_vote_dir)
        # Get Senate votes from files
        senate_votes_files = os.listdir(self.senate_vote_dir)
        senate_votes_files = [f for f in senate_votes_files if f.startswith('vote') and f.endswith('.json')]

        self.house_votes = []
        for vote_file in house_votes_files:
            with open(self.house_vote_dir + '/' + vote_file, 'r') as f:
                self.house_votes.append([json.load(f), int(vote_file.replace('roll', '').replace('.json', ''))])
        self.house_votes = sorted(self.house_votes, key=lambda x: x[1], reverse=True)

        self.senate_votes = []
        for vote_file in senate_votes_files:
            with open(self.senate_vote_dir + '/' + vote_file, 'r') as f:
                self.senate_votes.append([json.load(f), int(vote_file.replace('vote', '').replace('.json', ''))])
        self.senate_votes = sorted(self.senate_votes, key=lambda x: x[1], reverse=True)

    def draw_house_figure(self, meta, vote_set):
        figsize = 1.5
        radius = 0.9
        size = 0.2
        title = 'Roll call {}  ({})'.format(meta['rollcall-num'], meta['action-date'])
        if 'legis-num' in meta.keys():
            title += '\n{}'.format(meta['legis-num'])
        if 'vote-desc' in meta.keys() and meta['vote-desc'] != '':
            title += '\n{}'.format(wrap_text(['vote-desc'], 100))
        elif 'amendment-num' in meta.keys() and meta['amendment-num'] != '':
            title += '\nAmendment {}'.format(wrap_text(['amendment-num'], 100))
            title += '\nAuthor: {}'.format(wrap_text(['amendment-author'], 100))
        title += '\n{} ({})'.format(meta['vote-question'], meta['vote-type'])
        title += '\n{}'.format(meta['vote-result'])

        if 'totals-by-vote' in meta['vote-totals'][3].keys():
            fig = plt.figure(figsize=(7, 6))
            ax = plt.subplot2grid((2, 5), (0, 0), colspan=4, rowspan=2)
            ax2 = plt.subplot2grid((2, 5), (1, 4), colspan=1)
            ax.set_title(title)
            labels = ['Yes', 'No', 'Present', 'Not Voting']
            totals = meta['vote-totals'][3]['totals-by-vote']
            yes = int(totals['yea-total'])
            no = int(totals['nay-total'])
            present = int(totals['present-total'])
            not_voting = int(totals['not-voting-total'])
            total_votes = yes + no + present + not_voting
            sizes = [yes, no, present, not_voting]
            colors = ['#33FF33', '#CCCCCC', 'gray', 'white']
            pie = ax.pie(sizes, autopct='%d%%', pctdistance=0.9, colors=colors, counterclock=False, radius=radius,
                         labels=labels, shadow=False, startangle=-90, wedgeprops=dict(width=size, edgecolor='w'),
                         labeldistance=1.05)
            for i, a in enumerate(pie[2]):
                if float(a.get_text().strip('%')) < 2:
                    a.set_text('')
                    ax.texts[i*2].set_text('')
            ax.legend(pie[0], labels, bbox_to_anchor=(1, 0, 0.5, 1.75), loc="center left")

            # Create by party results nested pie chart
            dem_totals = [i['totals-by-party'] for i in meta['vote-totals'][0:3]
                          if i['totals-by-party']['party'] == 'Democratic']
            repub_totals = [i['totals-by-party'] for i in meta['vote-totals'][0:3]
                            if i['totals-by-party']['party'] == 'Republican']
            ind_totals = [i['totals-by-party'] for i in meta['vote-totals'][0:3]
                          if i['totals-by-party']['party'] == 'Independent']
            dem_votes = []
            rep_votes = []
            ind_votes = []
            results = []
            dem_votes.append(int(dem_totals[0]['yea-total']))
            rep_votes.append(int(repub_totals[0]['yea-total']))
            ind_votes.append(int(ind_totals[0]['yea-total']))
            results.append(int(dem_totals[0]['yea-total']))
            results.append(int(repub_totals[0]['yea-total']))
            results.append(int(ind_totals[0]['yea-total']))

            dem_votes.append(int(dem_totals[0]['nay-total']))
            rep_votes.append(int(repub_totals[0]['nay-total']))
            ind_votes.append(int(ind_totals[0]['nay-total']))
            results.append(int(dem_totals[0]['nay-total']))
            results.append(int(repub_totals[0]['nay-total']))
            results.append(int(ind_totals[0]['nay-total']))

            dem_votes.append(int(dem_totals[0]['present-total']))
            rep_votes.append(int(repub_totals[0]['present-total']))
            ind_votes.append(int(ind_totals[0]['present-total']))
            results.append(int(dem_totals[0]['present-total']))
            results.append(int(repub_totals[0]['present-total']))
            results.append(int(ind_totals[0]['present-total']))

            dem_votes.append(int(dem_totals[0]['not-voting-total']))
            rep_votes.append(int(repub_totals[0]['not-voting-total']))
            ind_votes.append(int(ind_totals[0]['not-voting-total']))
            results.append(int(dem_totals[0]['not-voting-total']))
            results.append(int(repub_totals[0]['not-voting-total']))
            results.append(int(ind_totals[0]['not-voting-total']))

            dem_max = max(dem_votes)
            dem_max_index = dem_votes.index(max(dem_votes))
            rep_max = max(rep_votes)
            rep_max_index = rep_votes.index(max(rep_votes))
            ind_max = max(ind_votes)
            ind_max_index = ind_votes.index(max(ind_votes))

            # Calculate the level of bipartisan agreement as a percentage of the total votes
            if sum(dem_votes) == 0:
                bipartisan = 0
            else:
                bipartisan = dem_max / sum(dem_votes)
            # Same index for max votes in two parties indicates agreement
            if sum(rep_votes) != 0 and dem_max_index == rep_max_index:
                bipartisan += rep_max / sum(rep_votes)
            elif sum(rep_votes) != 0:
                bipartisan = abs(bipartisan - (rep_max / sum(rep_votes)))
            if sum(ind_votes) > 0:
                if dem_max_index == ind_max_index:
                    bipartisan += ind_max / sum(ind_votes)
                else:
                    bipartisan = abs(bipartisan - (ind_max / sum(ind_votes)))
            bipartisan_percent = 50 * bipartisan

            party_labels = ['Democratic', 'Republican', 'Independent']
            inner_colors = ['blue', 'red', 'purple']
            pie = ax.pie(results, autopct='%d%%', pctdistance=0.85, colors=inner_colors, counterclock=False,
                         shadow=False, startangle=-90, radius=radius-size,
                         wedgeprops=dict(width=radius-size, edgecolor='w'))
            for i, a in enumerate(pie[2]):
                if results[i] >= 5:
                    a.set_text('{}'.format(results[i]))
                else:
                    a.set_text('')
            ax.set(aspect="equal")
            plt.legend(pie[0], party_labels, bbox_to_anchor=(-0.25, 0, 0, 2.95), loc="center left")

            # Create barchart
            ax2.bar([0], bipartisan_percent, width=1, bottom=None, color='black')
            plt.xticks([0])
            plt.yticks(np.arange(0, 101, 10))
            ax2.set_title('Bipartisan Percent\n{:.1f}%'.format(bipartisan_percent))
        elif 'totals-by-candidate' in meta['vote-totals'][3].keys():
            # The vote was special, not producing normal vote total counts
            fig = plt.figure(figsize=(8, 6))
            plt.title(title)
            vote_list = meta['vote-totals']
            vote_counts = []
            vote_for = []
            for item in vote_list:
                vote_for.append(item['totals-by-candidate']['candidate'])
                vote_counts.append(int(item['totals-by-candidate']['candidate-total']))
            pie = plt.pie(vote_counts, autopct='%d%%', counterclock=False, shadow=False, startangle=-90,
                          radius=radius, wedgeprops=dict(width=size, edgecolor='w'))
            for i, a in enumerate(pie[2]):
                if float(a.get_text().strip('%')) < 2:
                    a.set_text('')
            plt.legend(pie[0], vote_for, bbox_to_anchor=(1, 0, 0.5, 1), loc="center left")
            plt.tight_layout()

        plt.savefig('{}/roll{}.png'.format(self.images_dir, meta['rollcall-num']),
                    dpi=70*figsize, bbox_inches="tight", pad_inches=.02)
        plt.close()

    def draw_senate_figure(self, meta, vote_set):
        figsize = 1.5
        radius = 0.9
        size = 0.2
        title = 'Roll call {}  ({})'.format(meta['vote_number'], meta['vote_date'])
        if 'document' in meta.keys():
            title += '\n{} -- {}'.format(meta['document']['document_name'],
                                         wrap_text(meta['document']['document_title'], 100))
        title += '\n{} ({} required)'.format(meta['vote_question_text'], meta['majority_requirement'])
        title += '\n{}'.format(meta['vote_result'])
        fig = plt.figure(figsize=(7, 6))
        ax = plt.subplot2grid((2, 5), (0, 0), colspan=4, rowspan=2)
        ax2 = plt.subplot2grid((2, 5), (1, 4), colspan=1)
        ax.set_title(title)
        labels = ['Yes', 'No', 'Present', 'Not Voting']
        totals = meta['count']
        if totals['yeas'] != '':
            yes = int(totals['yeas'])
        else:
            yes = 0
        if totals['nays'] != '':
            no = int(totals['nays'])
        else:
            no = 0
        if totals['present'] != '':
            present = int(totals['present'])
        else:
            present = 0
        if totals['absent'] != '':
            not_voting = int(totals['absent'])
        else:
            not_voting = 0
        total_votes = yes + no + present + not_voting
        sizes = [yes, no, present, not_voting]
        colors = ['#33FF33', '#CCCCCC', 'gray', 'white']
        pie = ax.pie(sizes, autopct='%d%%', pctdistance=0.9, colors=colors, counterclock=False, radius=radius,
                     labels=labels, shadow=False, startangle=-90, wedgeprops=dict(width=size, edgecolor='w'),
                     labeldistance=1.05)
        for i, a in enumerate(pie[2]):
            if float(a.get_text().strip('%')) < 2:
                a.set_text('')
                ax.texts[i*2].set_text('')
        ax.legend(pie[0], labels, bbox_to_anchor=(1, 0, 0.5, 1.75), loc="center left")

        # Get the number of party votes
        party_votes = {'D': [], 'R': [], 'I': []}
        for party in ['D', 'R', 'I']:
            party_votes[party].append(len([i for i in vote_set['members']
                                          if (i['member']['party'] == party)
                                          and (i['member']['vote_cast'] in ['Yes', 'Yea', 'Aye', 'Y'])]))
            party_votes[party].append(len([i for i in vote_set['members']
                                          if (i['member']['party'] == party)
                                          and (i['member']['vote_cast'] in ['No', 'Nay', 'N'])]))
            party_votes[party].append(len([i for i in vote_set['members']
                                          if (i['member']['party'] == party)
                                          and (i['member']['vote_cast'] in ['Present', 'present'])]))
            party_votes[party].append(len([i for i in vote_set['members']
                                          if (i['member']['party'] == party)
                                          and (i['member']['vote_cast'] in ['Not Voting'])]))
        party_labels = ['Democratic', 'Republican', 'Independent']
        inner_colors = ['blue', 'red', 'purple']
        results = [party_votes['D'][0],
                   party_votes['R'][0],
                   party_votes['I'][0],
                   party_votes['D'][1],
                   party_votes['R'][1],
                   party_votes['I'][1],
                   party_votes['D'][2],
                   party_votes['R'][2],
                   party_votes['I'][2],
                   party_votes['D'][3],
                   party_votes['R'][3],
                   party_votes['I'][3]]

        pie = ax.pie(results, autopct='%d%%', pctdistance=0.85, colors=inner_colors, counterclock=False,
                     shadow=False, startangle=-90, radius=radius-size,
                     wedgeprops=dict(width=radius-size, edgecolor='w'))
        for i, a in enumerate(pie[2]):
            if results[i] >= 5:
                a.set_text('{}'.format(results[i]))
            else:
                a.set_text('')
        ax.set(aspect="equal")
        plt.legend(pie[0], party_labels, bbox_to_anchor=(-0.25, 0, 0, 2.95), loc="center left")

        dem_max = max(party_votes['D'])
        dem_max_index = party_votes['D'].index(max(party_votes['D']))
        rep_max = max(party_votes['R'])
        rep_max_index = party_votes['R'].index(max(party_votes['R']))
        ind_max = max(party_votes['I'])
        ind_max_index = party_votes['I'].index(max(party_votes['I']))

        dem_sum = sum(party_votes['D'])
        rep_sum = sum(party_votes['R'])
        ind_sum = sum(party_votes['I'])

        if dem_max_index == ind_max_index:
            dem_max += ind_max
            dem_sum += ind_sum
        elif rep_max_index == ind_max_index:
            rep_max += ind_max
            rep_sum += ind_sum

        # Calculate the level of bipartisan agreement as a percentage of the total votes
        bipartisan = dem_max / dem_sum
        # Same index for max votes in two parties indicates agreement
        if dem_max_index == rep_max_index:
            bipartisan += rep_max / rep_sum
        else:
            bipartisan = abs(bipartisan - (rep_max / rep_sum))
        # if sum(party_votes['I']) > 0:
        #     if dem_max_index == ind_max_index:
        #         bipartisan += ind_max / sum(party_votes['I'])
        #     else:
        #         bipartisan = abs(bipartisan - (ind_max / sum(party_votes['I'])))
        bipartisan_percent = 50 * bipartisan

        # Create barchart
        ax2.bar([0], bipartisan_percent, width=1, bottom=None, color='black')
        plt.xticks([0])
        plt.yticks(np.arange(0, 101, 10))
        ax2.set_title('Bipartisan Percent\n{:.1f}%'.format(bipartisan_percent))

        plt.savefig('{}/vote{}.png'.format(self.images_dir, meta['vote_number'].zfill(5)),
                    dpi=70*figsize, bbox_inches="tight", pad_inches=.02)
        plt.close()

    def insert_house_table_entry(self, meta, proc_item, procedural):
        if procedural is False:
            html_text = '<h3>Roll call vote {}</h3>\n'.format(meta['rollcall-num'])
        else:
            html_text = '<h3>Roll call vote {}  (<i>Procedural</i>)</h3>\n'.format(meta['rollcall-num'])
        html_text += '{} Congress'.format(meta['congress'])
        if 'chamber' in meta.keys():
            html_text += ' -- Chamber: {}'.format(meta['chamber'])
        elif 'committee' in meta.keys():
            html_text += ' -- Committee: {}'.format(meta['committee'])
        html_text += '<p>{}</p>\n'.format(meta['action-date'])
        doc_page = ''
        if 'legis-num' in meta.keys():
            html_text += '{}'.format(meta['legis-num'])
            bill = meta['legis-num'].split(' ')
            if len(bill) == 2 and bill[0] == 'S':
                # Senate bill
                doc_page = 'https://www.congress.gov/bill/{}th-congress/senate-bill/{}/text'\
                    .format(self.congress, bill[1])
            elif len(bill) == 3 and bill[0] == 'H' and bill[1] == 'R':
                doc_page = 'https://www.congress.gov/bill/{}th-congress/house-bill/{}/text'\
                    .format(self.congress, bill[2])
            elif len(bill) == 3 and bill[0] == 'H' and bill[1] == 'RES':
                doc_page = 'https://www.congress.gov/bill/{}th-congress/house-resolution/{}/text'\
                    .format(self.congress, bill[2])
            elif len(bill) == 4 and bill[0] == 'H' and bill[1] == 'CON' and bill[2] == 'RES':
                doc_page = 'https://www.congress.gov/bill/{}th-congress/house-resolution/{}/text'\
                    .format(self.congress, bill[3])
            elif len(bill) == 4 and bill[0] == 'H' and bill[1] == 'J' and bill[2] == 'RES':
                doc_page = 'https://www.congress.gov/bill/{}th-congress/house-joint-resolution/{}/text'\
                    .format(self.congress, bill[3])
            elif len(bill) == 4 and bill[0] == 'S' and bill[1] == 'J' and bill[2] == 'RES':
                doc_page = 'https://www.congress.gov/bill/{}th-congress/senate-joint-resolution/{}/text'\
                    .format(self.congress, bill[3])
        if 'vote-desc' in meta.keys() and meta['vote-desc'] != '':
            html_text += '<br>{}'.format(wrap_text(meta['vote-desc'], 100))
        elif 'amendment-num' in meta.keys() and meta['amendment-num'] != '':
            html_text += '<br>Amendment {}'.format(wrap_text(meta['amendment-num'], 100))
            html_text += '<br>Author: {}'.format(wrap_text(meta['amendment-author'], 100))
        html_text += '<br><br><font class="question">{}</font>'.format(meta['vote-question'])
        html_text += '<br><font class="result_{}"><b>{}</b></font> : {}'\
            .format(meta['vote-result'].replace(' ', '_'), meta['vote-result'], meta['vote-type'])
        html_text += '\n'
        if self.UPDATES_ONLY is not True or 'roll{}.png'.format(proc_item[1]) not in self.image_files:
            self.draw_house_figure(meta, proc_item[0]['rollcall-vote']['vote-data'])
        html_text += '<br><a href={}/{}><img src="{}/{}"></a>\n'.format(self.images_dir, 'roll{}.png'.format(proc_item[1]),
                                                                        self.images_dir, 'roll{}.png'.format(proc_item[1]))
        # Create the URL for the roll call page to process
        url = '{}{}.xml'.format(self.rollcall_url_base, meta['rollcall-num'])
        html_text += '<br><a href="{}">Roll call vote details</a>'.format(url)
        # Create link to document
        if doc_page != '':
            html_text += '<br><a href="{}">Document</a>'.format(doc_page)
        return html_text


    def insert_senate_table_entry(self, meta, proc_item, procedural):
        if procedural is False:
            html_text = '<h3>Roll call vote {}</h3>\n'.format(meta['vote_number'])
        else:
            html_text = '<h3>Roll call vote {}  (<i>Procedural</i>)</h3>\n'.format(meta['vote_number'])
        html_text += '{} Congress'.format(meta['congress'])
        html_text += '<p>{}</p>\n'.format(meta['vote_date'])
        amend_page = ''
        doc_page = ''
        if 'document' in meta.keys():
            doc_name = meta['document']['document_name']
            html_text += '{} -- {}'.format(doc_name, meta['document']['document_title'])
            if doc_name != '':
                # Create document link
                doc_page = ''
                bill = doc_name.split(' ')
                if len(bill) == 1:
                    if bill[0].startswith('PN'):
                        doc_page = 'https://www.congress.gov/nomination/{}th-congress/{}'.format(self.congress, bill[0][2:])
                elif len(bill) == 2:
                    if bill[0] == 'S.':
                        doc_page = 'https://www.congress.gov/bill/{}th-congress/senate-bill/{}/text'.format(self.congress, bill[1])
                    elif bill[0] == 'H.R.':
                        doc_page = 'https://www.congress.gov/bill/{}th-congress/house-bill/{}/text'.format(self.congress, bill[1])
                    elif bill[0] == 'S.J.Res.':
                        doc_page = 'https://www.congress.gov/bill/{}th-congress/'\
                                   'senate-joint-resolution/{}/text'\
                                    .format(self.congress, bill[1], bill[1], self.session)
        if 'amendment' in meta.keys():
            amend_number = meta['amendment']['amendment_number']
            if amend_number != '':
                number = amend_number.split(' ')[1]
                amend_page = 'https://www.congress.gov/amendment/{}th-congress/senate-amendment/{}'\
                    .format(self.congress, number)
                if doc_page == '':
                    bill = meta['amendment']['amendment_to_document_number'].split(' ')
                    if len(bill) == 1:
                        if bill[0].startswith('PN'):
                            doc_page = 'https://www.congress.gov/nomination/{}th-congress/{}'.format(self.congress, bill[0][2:])
                    elif len(bill) == 2:
                        if bill[0] == 'S.':
                            doc_page = 'https://www.congress.gov/bill/{}th-congress/senate-bill/{}'.format(self.congress, bill[1])
                        elif bill[0] == 'H.R.':
                            doc_page = 'https://www.congress.gov/bill/{}th-congress/house-bill/{}'.format(self.congress, bill[1])
                        elif bill[0] == 'S.J.Res.':
                            doc_page = 'https://www.congress.gov/bill/{}th-congress/'\
                                       'senate-joint-resolution/{}'\
                                        .format(self.congress, bill[1], bill[1], self.session)

        html_text += '\n<br>{}'.format(meta['vote_question_text'])
        if meta['vote_result_text'].find('Rejected') >= 0:
            result_class = 'Failed'
        elif meta['vote_result_text'].find('Passed') >= 0\
            or meta['vote_result_text'].find('Agreed to') >= 0\
            or meta['vote_result_text'].find('Confirmed') >= 0:
            result_class = 'Passed'
        else:
            result_class = 'generic'
        html_text += '<br><font class="result_{}"><b>{}</b></font> : {}'.format(result_class,
                                                                         meta['vote_result_text'],
                                                                         meta['majority_requirement'])
        html_text += '\n'
        if self.UPDATES_ONLY is not True or 'vote{}.png'.format(str(proc_item[1]).zfill(5)) not in self.image_files:
            self.draw_senate_figure(meta, proc_item[0]['roll_call_vote'])
        html_text += '<br><a href={}/{}><img src="{}/{}"></a>\n'\
            .format(self.images_dir, 'vote{}.png'.format(str(proc_item[1]).zfill(5)),
                    self.images_dir, 'vote{}.png'.format(str(proc_item[1]).zfill(5)))
        # Create the URL for the roll call page to process
        url = '{}{}'.format(self.base_url, str(meta['vote_number']).zfill(5))
        html_text += '<br><a href="{}">Roll call vote details</a>'.format(url)
        # Create link to document
        if amend_page != '':
            html_text += '<br><a href="{}">Amendment</a>'.format(amend_page)
        # Create link to document
        if doc_page != '':
            html_text += '<br><a href="{}">Document</a>'.format(doc_page)
        return html_text

    def process_votes(self):
        # Create an HTML page for the graphs
        html = '<html>\n<head>\n<title>Congress Votes {}</title>'.format(self.year)
        html += '\n<link rel="stylesheet" href="style.css">\n</head>\n'
        html += '<center><h1>Congress Votes {}</h1></center>\n'.format(self.year)
        html += '<body><center>\n<h2>Last updated {}</h2><br>\n'.format(dt.now().strftime('%B %d, %Y'))
        html += '<table>\n<th>House of Representative</th><th>Senate</th></tr>\n'
        house_index = 0
        senate_index = 0
        house_date = dt.now()
        senate_date = dt.now()
        while (house_index < len(self.house_votes)) or (senate_index < len(self.senate_votes)):
            html += '<tr>'
            if house_index < len(self.house_votes):
                house_date = self.house_votes[house_index][0]['rollcall-vote']['vote-metadata']['action-date']
                house_date = dt.strptime(house_date, '%d-%b-%Y')
            if senate_index < len(self.senate_votes):
                try:
                    senate_date = self.senate_votes[senate_index][0]['roll_call_vote']['vote_date']
                except TypeError:
                    html += '</td><td>Senate file error</td><tr>\n'
                    senate_index += 1
                    continue
                s = senate_date.split(' ')
                senate_date = '{}-{}-{}'.format(s[1].strip(','), s[0][0:3], s[2].strip(','))
                senate_date = dt.strptime(senate_date, '%d-%b-%Y')
            print('House index: {}, House date: {}'.format(house_index, house_date))
            print('Senate index: {}, Senate date: {}'.format(senate_index, senate_date))
            house = (senate_index == len(self.senate_votes)) or (house_date >= senate_date)
            senate = (house_index == len(self.house_votes)) or (senate_date >= house_date)
            if house_index < len(self.house_votes) and house:
                vote_meta = self.house_votes[house_index][0]['rollcall-vote']['vote-metadata']
                if vote_meta['vote-question'] in ['On Ordering the Previous Question',
                                                  'On Motion to Table',
                                                  'On Motion to Recommit with Instructions',
                                                  'On Motion to Commit with Instructions',
                                                  'On Motion to Table the Motion to Refer',
                                                  'On Motion to Fix the Convening Time',
                                                  'Call by States',
                                                  'Election of the Speaker',
                                                  'On Ordering a Call of the House',
                                                  'Call of the House',
                                                  'Table Appeal of the Ruling of the Chair',
                                                  'On Approving the Journal']:
                    html += '<td class="procedural">'
                    procedural = True
                else:
                    html += '<td>'
                    procedural = False
                html += self.insert_house_table_entry(vote_meta, self.house_votes[house_index], procedural)
                house_index += 1
            else:
                html += '<td>'
            html += '</td>\n'
            if senate_index < len(self.senate_votes) and senate:
                vote_meta = self.senate_votes[senate_index][0]['roll_call_vote']
                if vote_meta['vote_question_text'].startswith('On the Cloture Motion')\
                        or vote_meta['vote_question_text'].startswith('On the Decision of the Chair')\
                        or vote_meta['vote_question_text'].startswith('On Cloture ')\
                        or vote_meta['vote_question_text'].startswith('On the Motion to Proceed')\
                        or vote_meta['vote_question_text'].startswith('On the Motion to Table'):
                    html += '<td class="procedural">'
                    procedural = True
                else:
                    html += '<td>'
                    procedural = False
                html += self.insert_senate_table_entry(vote_meta, self.senate_votes[senate_index], procedural)
                senate_index += 1
            else:
                html += '<td>'
            html += '</td>\n'
            html += '</tr>\n'
        html += '</table>\n'
        html += '</center></body>\n</html>'
        with open('./congress_votes_{}.html'.format(self.year), 'wt') as f:
            f.write(html)


if __name__ == '__main__':
    process = ProcessCongressVotes(2019, True)
    process.process_votes()
