from math import inf
from operator import setitem
from unicodedata import normalize
from collections import namedtuple
from abc import ABC
import re

from bs4 import BeautifulSoup

from microlib import safeget

piratebay = 'https://www.thepiratebay3.to/s/'
kickasstorrents = 'https://kickasstorrents.to/search/'

Torrent = namedtuple('Torrent', [
    'name',
    'seeds',
    'leachs',
    'size',
    'type',
    'uploader',
    'magnet'
])


class TorrentBase(ABC):

    @classmethod
    def _getTorrentBase(cls, tor_div, tor_pt):
        pattern = getattr(cls, tor_pt)
        attr = tor_div.select_one(pattern)
        return attr.text if attr else None

    @classmethod
    def _getTorrentData(cls, tor_div):
        return Torrent(*map(
            lambda attr: getattr(
                cls, '_getTorrent' + attr.capitalize()
            )(cls, tor_div),
            Torrent._fields
        ))

    for attr in Torrent._fields:
        setitem(locals(), '_tor_pt_' + attr, '')
        setitem(
            locals(),
            '_getTorrent' + attr.capitalize(),
            lambda cls, div, attr=attr: cls._getTorrentBase(
                div, '_tor_pt_' + attr
            )
        )

    locals().pop('attr')


class PirateBay(TorrentBase):
    _types = (
        'audio',
        'video',
        'applications',
        'games',
        'porn'
    )
    _tor_pt_pagesn = 'div[align=center] > a'
    _tor_pt_divs = '#searchResult tr'
    _tor_pt_name = 'div.detName > a'
    _tor_pt_seeds = 'td[align=right]:nth-child(3)'
    _tor_pt_leachs = 'td[align=right]:nth-child(4)'
    _tor_pt_size = 'font.detDesc'
    _tor_pt_type = 'td.vertTh center a:first-child'
    _tor_pt_uploader = 'font.detDesc > a'
    _tor_pt_magnet = 'td > a:nth-child(2)'
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
        return len(self._soup.select(self._tor_pt_pagesn))

    def _getTorrentDivs(self):
        return self._soup.select(self._tor_pt_divs)

    def _getTorrentMagnet(self, torrent_div):
        magnet = torrent_div.select_one(self._tor_pt_magnet)
        return magnet.attrs.get('href') if magnet else None

    def _getTorrentSize(self, torrent_div):
        specs = torrent_div.select_one(self._tor_pt_size)
        if specs:
            text = normalize('NFKD', specs.text)
            match = self._size_rgx.search(text)
            s, u = match.group('size'), match.group('unit')
            return f'{s} {u}' if s and u else None

    def _scrapeiter(self):
        self._setResultSoup(0)
        npages = self._getPagesNumber()
        for i in range(npages):
            self._setResultSoup(i)
            for div in self._getTorrentDivs():
                tor_data = self._getTorrentData(div)
                if any(tor_data): yield tor_data


class KickassTorrents(TorrentBase):
    _types = []
    _tor_pt_pagesn = 'div.pages a:last-child'
    _tor_pt_divs = 'table.data > tbody > tr'
    _tor_pt_name = 'a.cellMainLink'
    _tor_pt_seeds = 'td:nth-child(5)'
    _tor_pt_leachs = 'td:nth-child(6)'
    _tor_pt_size = 'td:nth-child(2)'
    _tor_pt_type = 'div.torrentname span > a:first-child'
    _tor_pt_uploader = 'td:nth-child(3)'
    _tor_pt_magnet = ''

    def __init__(self, torrent_name):
        self.torrent_name = torrent_name
        self._soup = None

    def _getUrl(self, page):
        kat, tor = kickasstorrents, self.torrent_name
        return kat + f'/{tor}/{page}'

    def _getTorrentDivs(self):
        return self._soup.select(self._tor_pt_divs)

    def _getPagesNumber(self):
        npages = self._soup.select_one(self._tor_pt_pagesn)
        return npages.text if npages else None
        
    def _setResultSoup(self, page):
        kat_url = self._getUrl(page)
        resp = safeget(kat_url)
        assert resp, 'KickassTorrents response invalid'
        self._soup = BeautifulSoup(resp.content, 'html.parser')

    def _scrapeiter(self):
        self._setResultSoup(0)
        npages = self._getPagesNumber()
        for i in range(1, 4):
            self._setResultSoup(i)
            for div in self._getTorrentDivs():
                tor_data = self._getTorrentData(div)
                if any(tor_data): yield tor_data

if __name__ == '__main__':
    a = PirateBay('inception')
    print(next(iter(a)))
