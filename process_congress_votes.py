import os
import json
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime as dt

UPDATES_ONLY = True


def draw_house_figure(meta, vote_set):
    figsize = 1.5
    radius = 0.9
    size = 0.2
    title = 'Roll call {}  ({})'.format(meta['rollcall-num'], meta['action-date'])
    if 'legis-num' in meta.keys():
        title += '\n{}'.format(meta['legis-num'])
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
        bipartisan = dem_max / sum(dem_votes)
        # Same index for max votes in two parties indicates agreement
        if dem_max_index == rep_max_index:
            bipartisan += rep_max / sum(rep_votes)
        else:
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

    plt.savefig('{}/roll{}.png'.format(images_dir, meta['rollcall-num']),
                dpi=70*figsize, bbox_inches="tight", pad_inches=.02)
    plt.close()



def draw_senate_figure(meta, vote_set):
    figsize = 1.5
    radius = 0.9
    size = 0.2
    title = 'Roll call {}  ({})'.format(meta['vote_number'], meta['vote_date'])
    if 'document' in meta.keys():
        title += '\n{} -- {}'.format(meta['document']['document_name'], meta['document']['document_title'])
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
    results = []
    results.append(party_votes['D'][0])
    results.append(party_votes['R'][0])
    results.append(party_votes['I'][0])

    results.append(party_votes['D'][1])
    results.append(party_votes['R'][1])
    results.append(party_votes['I'][1])

    results.append(party_votes['D'][2])
    results.append(party_votes['R'][2])
    results.append(party_votes['I'][2])

    results.append(party_votes['D'][3])
    results.append(party_votes['R'][3])
    results.append(party_votes['I'][3])
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

    plt.savefig('{}/vote{}.png'.format(images_dir, meta['vote_number'].zfill(5)),
                dpi=70*figsize, bbox_inches="tight", pad_inches=.02)
    plt.close()


# House vote files directory
house_dir = 'house_votes'
# Senate vote files directory
senate_dir = 'senate_votes'
# Images directory
images_dir = 'images'

# Create the images directory if it is not found
try:
    os.listdir(images_dir)
except FileNotFoundError:
    os.mkdir(images_dir)
# Get list of existing image files
image_files = os.listdir(images_dir)
image_files = [f for f in image_files if f.endswith('.png')]

# Create the House votes directory if it is not found
try:
    os.listdir(house_dir)
except FileNotFoundError:
    os.mkdir(house_dir)
# Get House votes from files
house_votes_files = os.listdir(house_dir)
house_votes_files = [f for f in house_votes_files if f.startswith('roll') and f.endswith('.json')]

# Create the Senate votes directory if it is not found
try:
    os.listdir(senate_dir)
except FileNotFoundError:
    os.mkdir(senate_dir)
# Get Senate votes from files
senate_votes_files = os.listdir(senate_dir)
senate_votes_files = [f for f in senate_votes_files if f.startswith('vote') and f.endswith('.json')]


house_votes = []
for vote_file in house_votes_files:
    with open(house_dir + '/' + vote_file, 'r') as f:
        house_votes.append([json.load(f), int(vote_file.replace('roll', '').replace('.json', ''))])
house_votes = sorted(house_votes, key=lambda x: x[1], reverse=True)

senate_votes = []
for vote_file in senate_votes_files:
    with open(senate_dir + '/' + vote_file, 'r') as f:
        senate_votes.append([json.load(f), int(vote_file.replace('vote', '').replace('.json', ''))])
senate_votes = sorted(senate_votes, key=lambda x: x[1], reverse=True)

def insert_house_table_entry(html_text, meta, proc_item):
    html_text = '<h1>Roll call vote {}</h1>\n'.format(meta['rollcall-num'])
    html_text += '{} Congress'.format(meta['congress'])
    if 'chamber' in meta.keys():
        html_text += ' -- Chamber: {}'.format(meta['chamber'])
    elif 'committee' in meta.keys():
        html_text += ' -- Committee: {}'.format(meta['committee'])
    html_text += '<p>{}</p>\n'.format(meta['action-date'])
    if 'legis-num' in meta.keys():
        html_text += '{}'.format(meta['legis-num'])
    html_text += ' -- {}'.format(meta['vote-question'])
    html_text += '<br><b>{}</b> : {}'.format(meta['vote-result'], meta['vote-type'])
    html_text += '\n'
    if UPDATES_ONLY is not True or 'roll{}.png'.format(proc_item[1]) not in image_files:
        draw_house_figure(meta, proc_item[0]['rollcall-vote']['vote-data'])
    html_text += '<br><a href={}/{}><img src="{}/{}"></a>\n'.format(images_dir, 'roll{}.png'.format(proc_item[1]),
                                                                    images_dir, 'roll{}.png'.format(proc_item[1]))
    return html_text


def insert_senate_table_entry(html_text, meta, proc_item):
    html_text = '<h1>Roll call vote {}</h1>\n'.format(meta['vote_number'])
    html_text += '{} Congress'.format(meta['congress'])
    html_text += '<p>{}</p>\n'.format(meta['vote_date'])
    if 'document' in meta.keys():
        html_text += '{} -- {}'.format(meta['document']['document_name'], meta['document']['document_title'])
    html_text += ' -- {}'.format(meta['vote_question_text'])
    html_text += '<br><b>{}</b> : {}'.format(meta['vote_result_text'], meta['majority_requirement'])
    html_text += '\n'
    if UPDATES_ONLY is not True or 'vote{}.png'.format(str(proc_item[1]).zfill(5)) not in image_files:
        draw_senate_figure(meta, proc_item[0]['roll_call_vote'])
    html_text += '<br><a href={}/{}><img src="{}/{}"></a>\n'.format(images_dir, 'vote{}.png'.format(str(proc_item[1]).zfill(5)),
                                                                    images_dir, 'vote{}.png'.format(str(proc_item[1]).zfill(5)))
    return html_text


# Create an HTML page for the graphs
html = '<html>\n<head>\n<title>House Votes</title>\n<link rel="stylesheet" href="style.css">\n</head>\n<body>\n'
html += '<table>\n<th>House of Representative</th><th>Senate</th></tr>\n'
house_index = 0
senate_index = 0
house_date = dt.now()
senate_date = dt.now()
while (house_index < len(house_votes)) or (senate_index < len(senate_votes)):
    html += '<tr>'
    html += '<td>'
    if house_index < len(house_votes):
        house_date = house_votes[house_index][0]['rollcall-vote']['vote-metadata']['action-date']
        house_date = dt.strptime(house_date, '%d-%b-%Y')
    if senate_index < len(senate_votes):
        senate_date = senate_votes[senate_index][0]['roll_call_vote']['vote_date']
        s = senate_date.split(' ')
        senate_date = '{}-{}-{}'.format(s[1].strip(','), s[0][0:3], s[2].strip(','))
        senate_date = dt.strptime(senate_date, '%d-%b-%Y')
    print('House index: {}, House date: {}'.format(house_index, house_date))
    print('Senate index: {}, Senate date: {}'.format(senate_index, senate_date))
    house = (senate_index == len(senate_votes)) or (house_date >= senate_date)
    senate = (house_index == len(house_votes)) or (senate_date >= house_date)
    if house_index < len(house_votes) and house:
        vote_meta = house_votes[house_index][0]['rollcall-vote']['vote-metadata']
        html += insert_house_table_entry(html, vote_meta, house_votes[house_index])
        house_index += 1
    html += '</td>\n'
    html += '<td>'
    if senate_index < len(senate_votes) and senate:
        vote_meta = senate_votes[senate_index][0]['roll_call_vote']
        html += insert_senate_table_entry(html, vote_meta, senate_votes[senate_index])
        senate_index += 1
    html += '</td>\n'
    html += '</tr>\n'
html += '</table>\n'
html += '</body>\n</html>'
with open('./house_votes.html', 'wt') as f:
    f.write(html)
