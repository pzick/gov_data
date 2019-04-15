import requests
import calendar
from datetime import datetime as dt

# Format in: Congress(number), year, month(00), day(00), year, month, day
base_url = 'https://www.congress.gov/{}/crec/{}/{}/{}/CREC-{}-{}-{}.pdf'
year = 2019

Congress_start_year = 1787
Sessions_per_Congress = 2

# Subtract the start of Congress year 1787 from the year of interest, divide by two for the Congress number
congress = (year - Congress_start_year) / Sessions_per_Congress
# If the vote year calculated ends with .5, it is the second session, otherwise it is the first session
if congress > int(congress):
    session = 2
    congress = int(congress)
else:
    session = 1
    congress = int(congress)

today = dt.now()

html_text = '<!DOCTYPE html>\n<html>\n'
html_text += '<head><title>Congressional Records {}</title></head>\n'.format(year)
html_text += '<body>\n'

for month in range(1, 13):
    if month > today.month:
        break
    month_name = calendar.month_name[month]
    html_text += '<h2>{} {}</h2>\n'.format(month_name, year)
    for day in range(1, 32):
        if month == today.month and day > today.day:
            break
        try:
            day_name = calendar.day_name[calendar.weekday(year, month, day)]
        except ValueError:
            # The day is out of range for the month, skip it
            continue
        month_str = str(month).zfill(2)
        day_str = str(day).zfill(2)
        url = base_url.format(congress, year, month_str, day_str, year, month_str, day_str)
        r = requests.get(url)
        if r.status_code == 200:
            html_text += '<a href="{}">{}</a><br>\n'\
                .format(url, 'Congressional Record for {}, {} {}, {}'.format(day_name, month_name, day, year))
            print(url)
    html_text += '<br>\n'
html_text += '</body>\n</html>\n'
with open('Congressional_Records_{}.html'.format(year), 'wt') as f:
    f.write(html_text)
