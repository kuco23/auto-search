import os
from io import BytesIO
import argparse
from zipfile import ZipFile
from urllib.parse import urlsplit, parse_qs
from bs4 import BeautifulSoup
from microlib import safeget

SUBTITLES = 'https://www.podnapisi.net'
WDIR = os.getcwd()
if not os.path.isdir('subs'): os.mkdir('subs')

args = argparse.ArgumentParser(description='subtitles specs')
args.add_argument('mname', metavar='movie name', type=str)
args.add_argument('-lang', metavar='subtitle language', type=str, 
                  nargs='+', default='en', choices=['en', 'sl'])
vals = args.parse_args()

# get subtitles
url = SUBTITLES + '/en/subtitles/search/'
query_page = safeget(url, params = {'keywords': vals.mname})
assert query_page, 'Subtitles Response Not Valid'

# filter results
soup = BeautifulSoup(query_page.content, 'html.parser')
subtitles = soup.select('table.table > tbody tr')
for subtitle in subtitles:
    lang = subtitle.select_one('td:nth-child(4) > a').attrs['href']
    lang = parse_qs(urlsplit(lang).query)['language'][0]
    if lang in vals.lang:
        link = subtitle.select_one('div.pull-left > a').attrs['href']
        file = safeget(SUBTITLES + link)
        if not file: continue
        ZipFile(BytesIO(file.content)).extractall(WDIR + '/subs')
        if input('continue? y/n: ') == 'n': break
