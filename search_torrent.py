import re
from math import inf
from collections import namedtuple
from unicodedata import normalize

from bs4 import BeautifulSoup

from microlib import safeget

piratebay = 'https://www.thepiratebay3.to/s/'

Torrent = namedtuple('str', [
    'name',
    'seeds',
    'leachs',
    'size',
    'type',
    'uploader',
    'magnet'
])

class PirateBay:
    _types = (
        'audio',
        'video',
        'applications',
        'games',
        'porn'
    )
    _tor_pages_pt = 'div[align=center] > a'
    _tor_div_pt = '#searchResult tr'
    _tor_name_pt = 'div.detName > a'
    _tor_seeds_pt = 'td[align=right]:nth-child(3)'
    _tor_leachs_pt = 'td[align=right]:nth-child(4)'
    _tor_specs_pt = 'font.detDesc'
    _tor_type_pt = 'td.vertTh center a:first-child'
    _tor_uploader_pt = 'font.detDesc > a'
    _tor_magnet_pt = 'td > a:nth-child(2)'
    _size_rgx = re.compile(
        r'Size (?P<size>[\d\.]+) (?P<unit>\w+)'
    )

    def __init__(self, torrent_name, types=_types):
        self.torrent_name = torrent_name
        self.types = types
        self._soup = None

    def __iter__(self):
        yield from self._scrapeiter()
        

    def _getPayload(self, page):
        nm, tps = self.torrent_name, self.types
        tp_params = {tp: 'on' for tp in tps}
        return {'q': nm, 'page': page, **tp_params}
    

    def _setResultSoup(self, page):
        payload = self._getPayload(page)
        resp = safeget(piratebay, params=payload)
        assert resp, 'Pirate Bay response invalid'
        self._soup = BeautifulSoup(resp.content, 'html.parser')
        

    def _getPagesNumber(self):
        return len(self._soup.select(self._tor_pages_pt))

    def _getTorrentDivs(self):
        return self._soup.select(self._tor_div_pt)

    def _getTorrentName(self, torrent_div):
        name = torrent_div.select_one(self._tor_name_pt)
        return name.text if name else None
    
    def _getTorrentSeeds(self, torrent_div):
        seeds = torrent_div.select_one(self._tor_seeds_pt)
        return seeds.text if seeds else None
    
    def _getTorrentLeachs(self, torrent_div):
        leachs = torrent_div.select_one(self._tor_leachs_pt)
        return leachs.text if leachs else None

    def _getTorrentType(self, torrent_div):
        tp = torrent_div.select_one(self._tor_type_pt)
        return tp.text if tp else None

    def _getTorrentUploader(self, torrent_div):
        uploader = torrent_div.select_one(self._tor_uploader_pt)
        return uploader.text if uploader else None

    def _getTorrentMagnet(self, torrent_div):
        magnet = torrent_div.select_one(self._tor_magnet_pt)
        return magnet.attrs.get('href') if magnet else None

    def _getTorrentSize(self, torrent_div):
        specs = torrent_div.select_one(self._tor_specs_pt)
        if specs:
            text = normalize('NFKD', specs.text)
            match = self._size_rgx.search(text)
            s, u = match.group('size'), match.group('unit')
            return s + u if s and u else None

    def _getTorrentData(self, torrent_div):
        return Torrent(
            self._getTorrentName(torrent_div),
            self._getTorrentSeeds(torrent_div),
            self._getTorrentLeachs(torrent_div),
            self._getTorrentSize(torrent_div),
            self._getTorrentType(torrent_div),
            self._getTorrentUploader(torrent_div),
            self._getTorrentMagnet(torrent_div)
        )


    def _scrapeiter(self):
        self._setResultSoup(0)
        npages = self._getPagesNumber()
        for i in range(npages):
            self._setResultSoup(i)
            for div in self._getTorrentDivs():
                tor_data = self._getTorrentData(div)
                if any(tor_data): yield tor_data


if __name__ == '__main__':
    a = PirateBay('scott pilgrim')
    print(next(iter(a)))
