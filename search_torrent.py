from operator import setitem
from unicodedata import normalize
from collections import namedtuple
from abc import ABC
import re

from bs4 import BeautifulSoup, Tag

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


class TorrentSearchBase(ABC):

    @classmethod
    def __getTorrentBase(cls, tor_div, tor_pt: Tag):
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
            lambda cls, div, attr=attr: cls.__getTorrentBase(
                div, '_tor_pt_' + attr
            )
        )

    locals().pop('attr')
    

class PirateBaySearch(TorrentSearchBase):
    
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
    
    _types = (
        'audio',
        'video',
        'applications',
        'games',
        'porn'
    )
    
    def __init__(self, torrent_name, types=_types):
        self.torrent_name = torrent_name
        self.types = types
        
        self._soup = None
        self._npages = None

        self._setResultSoup(0)
        self._setPagesNumber()

    def __iter__(self):
        yield from self._torrentiter()

    def _getPayload(self, page):
        nm, tps = self.torrent_name, self.types
        tp_params = {tp: 'on' for tp in tps}
        return {'q': nm, 'page': page, **tp_params}

    def _setResultSoup(self, page):
        payload = self._getPayload(page)
        resp = safeget(piratebay, params=payload)
        assert resp, 'Pirate Bay response invalid'
        self._soup = BeautifulSoup(resp.content, 'html.parser')

    def _setPagesNumber(self):
        pagination = self._soup.select(self._tor_pt_pagesn)
        self._npages = len(pagination)

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

    def _pageiter(self):
        yield
        for i in range(1, self._npages):
            self._setResultSoup(i)
            yield

    def _torrentiter(self):
        for _ in self._pageiter():
            for div in self._getTorrentDivs():
                tor_data = self._getTorrentData(div)
                if any(tor_data): yield tor_data
                

if __name__ == '__main__':

    from math import inf
    from argparse import ArgumentParser

    args = ArgumentParser()
    args.add_argument(
        'tor_name', metavar='torrent name',
        type=str
    )
    args.add_argument(
        '-tp', metavar='torrent type',
        type=str, nargs='+',
        choices=PirateBaySearch._types,
        default=PirateBaySearch._types
    )
    args.add_argument(
        '-n', metavar='number of torrents',
        type=int, default=10
    )
    args.add_argument(
        '-mns', metavar='min torrent size',
        type=int, default=0
    )
    args.add_argument(
        '-mxs', metavar='max torrent size',
        type=int, default=inf
    )
    vals = args.parse_args()

    size_dict = {'KiB': 10**(-3), 'MiB': 1, 'GiB': 1 << 10}
    search_obj = PirateBaySearch(vals.tor_name, vals.tp)

    results = []
    for torrent in search_obj:
        size, unit = torrent.size.split()
        sizeMiB = float(size) * size_dict[unit]
        if (torrent.type.lower() in vals.tp and
            vals.mns <= sizeMiB <= vals.mxs
        ):
            results.append(torrent)
            if len(results) == vals.n:
                break

    print(results)
