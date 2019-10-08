import re
from collections import namedtuple
from unicodedata import normalize

from pandas import DataFrame
from bs4 import BeautifulSoup

from microlib import safeget

piratebay = 'https://www.thepiratebay3.to/s/'

data_template = namedtuple('str', [
    'torrent_name',
    'torrent_link',
    'torrent_seeds',
    'torrent_leachs',
    'torrent_size'
])

class PirateBay:
    _types = ('audio', 'video', 'applications', 'games', 'porn')
    _tor_div_pt = '#searchResult tr'
    _tor_name_pt = 'div.detName > a'
    _tor_seeds_pt = 'td[align=right]:nth-child(3)'
    _tor_leachs_pt = 'td[align=right]:nth-child(4)'
    _tor_specs_pt = 'font.detDesc'
    _size_rgx = re.compile(r'Size (?P<size>[\d\.]+) (?P<unit>\w+)')

    def __init__(self, torrent_name, types=_types):
        self.torrent_name = torrent_name
        self.types = types
        self._page = 0
        self._soup = None
        self._torrent_divs = None

    @property
    def _payload(self):
        nm, tps, pg = self.torrent_name, self.types, self._page
        return {'q': nm, 'page': pg, **{tp: 'on' for tp in tps}}
                    
    def _setPageSoup(self, page):
        resp = safeget(piratebay, params=self._payload, timeout=1)
        assert resp, 'Pirate Bay response invalid'
        self._soup = BeautifulSoup(resp.content, 'html.parser')

    def _setTorrentDivs(self):
        self._torrent_divs = self._soup.select(self._tor_div_pt)
        
    def _getTorrentName(self, torrent_div):
        name = torrent_div.select_one(self._tor_name_pt)
        return name.text if name else None
    
    def _getTorrentSeeds(self, torrent_div):
        seeds = torrent_div.select_one(self._tor_seeds_pt)
        return seeds.text if seeds else None
    
    def _getTorrentLeachs(self, torrent_div):
        leachs = torrent_div.select_one(self._tor_leachs_pt)
        return leachs.text if leachs else None
    
    def _getTorrentSize(self, torrent_div):
        specs = torrent_div.select_one(self._tor_specs_pt)
        if not specs: return
        text = normalize('NFKD', specs.text)
        match = self._size_rgx.search(text)
        size, unit = match.group('size'), match.group('unit')
        return size + unit if size and unit else None
        
    def _getTorrentData(self, torrent_div):
        return data_template(
            self._getTorrentName(torrent_div),
            None,
            self._getTorrentSeeds(torrent_div),
            self._getTorrentLeachs(torrent_div),
            self._getTorrentSize(torrent_div)
        )

    def scrape(self, num):
        data = []
        while num > 0:
            self._setPageSoup(self._page)
            self._page += 1
            self._setTorrentDivs()
            for _, div in zip(range(num), self._torrent_divs):
                data.append(self._getTorrentData(div))
                num -= 1
        return DataFrame(data, columns=data_template._fields)

if __name__ == '__main__':
    a = PirateBay('inception')
    sc = a.scrape(10)
    print(sc)
