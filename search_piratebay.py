from math import inf
from unicodedata import normalize
import os, argparse, re

from bs4 import BeautifulSoup
from pandas import DataFrame

from microlib import safeget, log

TORRENT_TYPES = ('audio', 'video', 'applications', 'games', 'porn')
UNIT2NUM = {'KiB' : 10**(-3), 'MiB' : 1, 'GiB' : 10**3} # std unit is MiB
LOG_FILE = 'magnet.log'

# set the terminal argument parser
args = argparse.ArgumentParser(description='torrent specs')
args.add_argument('tname', metavar='torrent_name', type=str)
args.add_argument('-typ', metavar='torrent_type', type=str,
                  nargs='+', choices=TORRENT_TYPES, default=[])
args.add_argument('-msd', metavar='minseeds', type=int, default=0)
args.add_argument('-mlc', metavar='minleachs', type=int, default=0)
args.add_argument('-msz', metavar='minsize_MiB', type=int, default=0)
args.add_argument('-xsz', metavar='maxsize_MiB', type=int, default=inf)
vals = args.parse_args()

# get the page containing torrents
url = 'https://thepiratebay3.org/index.php'
payload = {'q': vals.tname, **{typ: 'on' for typ in vals.typ}}
query_page = safeget(url, params = payload)
assert query_page, 'Pirate Bay Response Not Valid'

# filter the data to find an acceptable torrents (magnet links)
magnets, torrent_data = [], []
szrgx = re.compile(r'Size (?P<size>[\d\.]+) (?P<unit>KiB|MiB|GiB)')
soup = BeautifulSoup(query_page.content, 'html.parser')
torrents = soup.select('#searchResult tr')
for torrent in torrents:
    peers = torrent.select('td[align=right]')
    specs = torrent.select_one('font.detDesc')
    if not all((peers, specs)): continue
    seeds, leachs = (int(x.text) for x in peers)
    specs = szrgx.search(normalize('NFKD', specs.text))
    size = float(specs.group('size')) * UNIT2NUM[specs.group('unit')]
    if seeds >= vals.msd and leachs >= vals.mlc and \
       vals.msz <= size <= vals.xsz:
        name = torrent.select_one('div.detName > a').text
        torrent_data.append((name, seeds, leachs, size))
        magnet = torrent.select_one('td:nth-child(2) > a').attrs['href']
        magnets.append(magnet)

# print the available torrent data
cols = ('name', 'seeds', 'leachs', 'size')
print(DataFrame(torrent_data, columns=cols))

# ask user for magnet link index
try: idx = int(input('get magnet <index>: '))
except ValueError: exit()
if 0 <= idx < len(magnets):
    os.system('start ' + magnets[idx])
    log(magnets[idx], LOG_FILE)
