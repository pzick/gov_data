import os
import json

year = 2019
file_directory = 'data/congress_bills_{}'.format(year)
file_list = os.listdir(file_directory)

data_list = []
for name in file_list:
    if name.endswith('.json'):
        with open(file_directory + '/' + name, 'r') as f:
            data = json.load(f)
        data_list.append([name, data])

total = 0
passed = 0
law = 0
introduced = 0
referred = 0
confirmed = 0
calendar = 0
law_list = []
confirmed_list = []
judges = 0
mil_af = 0
mil_navy = 0
mil_marines = 0
mil_army = 0
for item in data_list:
    if 'bill_data' in item[1].keys() and 'last_bill' in item[1]['bill_data']:
        number = item[1]['bill_data']['last_bill']
        for bill in item[1]['bill_data']['bill']:
            if 'status' in bill.keys():
                if bill['status'].find('Agreed to') >= 0:
                    passed += 1
                elif bill['status'].find('Became Law') >= 0:
                    law += 1
                    law_list.append(bill['title'])
                elif bill['status'].find('Introduced') >= 0:
                    introduced += 1
                elif bill['status'].find('referred to') >= 0:
                    referred += 1
                elif bill['status'].find('Referred to') >= 0:
                    referred += 1
                elif bill['status'].find('Calendar') >= 0:
                    calendar += 1
            elif 'latest_action' in bill.keys():
                if bill['latest_action'].find('referred to') >= 0:
                    referred += 1
                elif bill['latest_action'].find('Confirmed') >= 0:
                    confirmed += 1
                    confirmed_list.append(bill['title'])
                    if bill['title'].find('for The Judiciary') >= 0:
                        judges += 1
                    elif bill['title'].find('Air Force') >= 0:
                        mil_af += 1
                    elif bill['title'].find('Army') >= 0:
                        mil_army += 1
                    elif bill['title'].find('Navy') >= 0:
                        mil_navy += 1
                    elif bill['title'].find('Marine Corps') >= 0:
                        mil_marines += 1
                elif bill['latest_action'].find('Calendar') >= 0:
                    calendar += 1
        print('{}  {}'.format(number, item[0].replace('.json','')))
        total += number
print('\nTotal = {}\n'.format(total))
print('{} became law'.format(law))
print('{} confirmed (total)'.format(confirmed))
print('    {} judges confirmed'.format(judges))
print('    {} Army confirmations'.format(mil_army))
print('    {} Navy confirmations'.format(mil_navy))
print('    {} Marine Corps confirmations'.format(mil_marines))
print('    {} Air Force confirmations'.format(mil_af))
print('{} passed chamber'.format(passed))
print('{} referred to committee'.format(referred))
print('{} on calendar'.format(calendar))
print('{} introduced'.format(introduced))

print('\nBecame Law ({})\n-------------------'.format(law))
for item in law_list:
    print(item)

print('\nConfirmed ({})\n-------------------'.format(confirmed))
for item in confirmed_list:
    print(item)
