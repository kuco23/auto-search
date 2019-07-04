from unicodedata import normalize
from math import inf
import os, argparse, re
from bs4 import BeautifulSoup
from microlib import safeget, log

PIRATE_BAY = 'https://thepiratebay3.org'
UNIT2NUM = {'KiB' : 10**(-3), 'MiB' : 1, 'GiB' : 10**3} # std unit is MiB
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

# filter the data to find an acceptable torrents (magnet links)
magnets = []
szrgx = re.compile(rf'Size (?P<size>[\d\.]+) (?P<unit>KiB|MiB|GiB)')
soup = BeautifulSoup(query_page.content, 'html.parser')
torrents = soup.select('#searchResult tr')
for torrent in torrents:
    peers_data = torrent.select('td[align=right]')
    specs = torrent.select_one('font.detDesc')
    if not all((peers_data, specs)): continue
    seeds, leachs = (int(x.text) for x in peers_data)
    specs = szrgx.search(normalize('NFKD', specs.text))
    size = float(specs.group('size')) * UNIT2NUM[specs.group('unit')]
    if seeds >= vals.msd and leachs >= vals.mlc and \
       vals.msz <= size <= vals.xsz:
        magnet = torrent.select_one('td:nth-child(2) > a').attrs['href']
        print(len(magnets), seeds, leachs, str(size) + ' MiB', sep=' - ')
        magnets.append(magnet)

# ask user for magnet link index
idx = input('get magnet <index>: ')
os.system('start ' + magnets[idx])
log(magnets[idx], LOG_FILE)
