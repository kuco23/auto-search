from unicodedata import normalize
from math import inf
import os, argparse, re
from bs4 import BeautifulSoup
from microlib import safeget, log

PIRATE_BAY = 'https://thepiratebay3.org'
UNIT2NUM = {'MiB' : 1, 'GiB' : 10**3} # std unit is MiB
LOG_FILE = 'magnet.log'

# set the terminal argument parser
args = argparse.ArgumentParser(description='torrent specs')
args.add_argument('tname', metavar='torrent_name', type=str)
args.add_argument('-msd', metavar='minseeds', type=int, default=0)
args.add_argument('-mlc', metavar='minleachs', type=int, default=0)
args.add_argument('-msz', metavar='minsize_MiB', type=int, default=0)
args.add_argument('-xsz', metavar='maxsize_MiB', type=int, default=inf)
vals = args.parse_args()

# get the page containing torrents
url = PIRATE_BAY + '/index.php'
query_page = safeget(url, params = {'q' : vals.tname})
assert query_page, 'Pirate Bay Response Not Valid'

# filter the data to find an acceptable torrent
szrgx = re.compile(r'Size (?P<size>[\d\.]+) (?P<unit>GiB|MiB)')
soup = BeautifulSoup(query_page.content, 'html.parser')
torrents = soup.select('#searchResult tr')
torrents.pop(0)
for torrent in torrents:
    seeds, leachs = (int(x.text) for x in torrent.select('td[align=right]'))
    specs = torrent.select_one('font.detDesc').text
    specs = szrgx.search(normalize('NFKD', specs))
    size = float(specs.group('size')) * UNIT2NUM[specs.group('unit')]
    if seeds >= vals.msd and leachs >= vals.mlc and \
       vals.msz <= size <= vals.xsz:
        magnet = torrent.select_one('td:nth-child(2) > a').attrs['href']
        os.system('start ' + magnet)
        if input('ok? y/n: ') == 'y':
            log(magnet, LOG_FILE)
            break
