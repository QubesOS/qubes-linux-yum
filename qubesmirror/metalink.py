#!/usr/bin/env python3
#
# qubesmirror -- a simple mirror manager for yum repos
# Copyright (C) 2015-2018  Wojtek Porczyk <woju@invisiblethingslab.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

'''Metalink generator'''

import argparse
import collections
import datetime
import hashlib
import pathlib
import posixpath
import sys

import jinja2
import lxml.etree

from . import get_common_parser
from . import __version__ as _version

XML_NAMESPACES = {
    'metalink3': 'http://www.metalinker.org/',
    'mm0': 'http://fedorahosted.org/mirrormanager',
    'repomd': 'http://linux.duke.edu/metadata/repo',
}

DEFAULT_HASHES = [
    'md5',
    'sha1',
    'sha256',
    'sha512',
    'ripemd160',
]

METALINK3 = jinja2.Template('''\
<?xml version="1.0" encoding="utf-8"?>
<metalink version="3.0"
        generator="{{ generator }}"
        pubdate="{{ utcnow.strftime('%a, %d %b %Y %H:%M:%S GMT') }}"
        xmlns="http://www.metalinker.org/"
        xmlns:mm0="http://fedorahosted.org/mirrormanager">

    <files>
        <file name="{{ file.path.name }}">
            <mm0:timestamp>{{ file.timestamp }}</mm0:timestamp>
            <size>{{ file.stat.st_size }}</size>
            {%- if file.alternates %}
            <mm0:alternates>
                {%- for alternate in file.alternates %}
                <mm0:alternate>
                    <mm0:timestamp>{{ alternate.timestamp }}</mm0:timestamp>
                    <size>{{ alternate.size }}</size>
                    <verification>
                    {%- for hashtype, hash in alternate.hashes %}
                        <hash type="{{ hashtype }}">{{ hash }}</hash>
                    {%- endfor %}
                    </verification>
                </mm0:alternate>
                {%- endfor %}
            </mm0:alternates>
            {%- endif %}
            <verification>
            {%- for hashtype in hashtypes %}
                <hash type="{{ hashtype }}">{{ file.get_hash(hashtype) }}</hash>
            {%- endfor %}
            </verification>

            <resources maxconnections="1">
            {%- for url in urls %}
                <url>{{ url }}</url>
            {%- endfor %}
            </resources>
        </file>
    </files>
</metalink>
''')

#
# RFC5854-compliant metalink, in case someone in Fedora decided to update
#
METALINK4 = jinja2.Template('''\
<?xml version="1.0" encoding="utf-8"?>
<metalink
        xmlns="urn:ietf:params:xml:ns:metalink"
        xmlns:mm0="http://fedorahosted.org/mirrormanager">
    <generator>{{ generator }}</generator>
    <published>{{ utcnow.strftime('%Y-%m-%dT%H:%M:%SZ') }}</published>

    <files>
        <file name="{{ file.path.name }}">
            <mm0:timestamp>{{ file.timestamp }}</mm0:timestamp>
            <size>{{ file.stat.st_size }}</size>
            {%- for hashtype in hashtypes %}
            <hash type="{{ hashtype }}">{{ file.get_hash(hashtype) }}</hash>
            {%- endfor %}

            {%- for url in urls %}
            <url>{{ url }}</url>
            {%- endfor %}
        </file>
    </files>
</metalink>
''')

class RepoMD:
    '''A representation of repomd.xml file'''

    class Alternate(collections.namedtuple('_Alternate',
            ('timestamp', 'size', 'hashes'))):
        # keep timestamp first, because is has to be sorted by it

        '''An alternate for fedora's metalink'''

        @classmethod
        def from_xml3(cls, xml):
            '''Load a single alternate from XML node.

            This can be either ``<file>`` or ``<mm0:alternate>``.
            '''
            return cls(
                timestamp=int(xml.xpath('./mm0:timestamp',
                    namespaces=XML_NAMESPACES)[0].text),
                size=int(xml.xpath('./metalink3:size',
                    namespaces=XML_NAMESPACES)[0].text),
                hashes=tuple((e.get('type'), e.text) for e in xml.xpath(
                    './metalink3:verification/metalink3:hash',
                    namespaces=XML_NAMESPACES)))

        @classmethod
        def parse_metalink3(cls, path):
            '''Read metalink file and yield all versions as alternates'''

            (xml,) = lxml.etree.parse(str(path)).xpath(
                '/metalink3:metalink/metalink3:files/metalink3:file',
                namespaces=XML_NAMESPACES)

            yield cls.from_xml3(xml)
            for alternate in xml.xpath('./mm0:alternates/mm0:alternate',
                    namespaces=XML_NAMESPACES):
                yield cls.from_xml3(alternate)

    def __init__(self, path):
        self.path = path
        self.stat = self.path.stat()
        assert self.stat.st_size < 1e7, 'memory protection safeguard'
        # the assert is because we read the file into memory:
        self.contents = self.path.read_bytes()
        self.timestamp = self._get_timestamp()
        self._alternates = set()

    @property
    def alternates(self):
        '''Alternates is proper order'''
        return sorted(self._alternates, reverse=True)

    def _get_timestamp(self):
        xml = lxml.etree.XML(self.contents)
        return max(int(e.text)
            for e in xml.xpath('/repomd:repomd/repomd:data/repomd:timestamp',
                namespaces=XML_NAMESPACES))

    def get_hash(self, algo):
        '''Get a hash of the contents of the file.'''
        return hashlib.new(algo, self.contents).hexdigest()

    def get_urls_for_mirrors(self, base, mirrors):
        '''Given base path and list of mirrors, yield all urls for mirrors.

        Mirrors which apparently do not mirror this repo are silently dropped.
        '''
        for mirror in mirrors:
            try:
                relpath = self.path.relative_to(base / mirror.subdir)
            except ValueError:
                # path is not inside base/subdir, so it is not mirrored here
                continue
            yield posixpath.join(mirror.url, str(relpath))

    def load_alternates(self, path, *, max_count, max_age):
        '''Given old metalink, load alternates from it.

        :param pathlib.Path path: path to old metalink
        :param int max_count: maximum number of loaded alternates
        :param int max_age: maximum age in seconds
        '''

        alternates = []
        for alt in self.Alternate.parse_metalink3(path):
            if alt.timestamp == self.timestamp:
                continue
            if max_age > 0 and alt.timestamp + max_age < self.timestamp:
                continue
            alternates.append(alt)
        alternates.sort(reverse=True)
        if max_count > 0:
            alternates = alternates[:max_count]
        self._alternates.update(alternates)

parser = get_common_parser()

parser.add_argument('--metalink', '-3',
    action='store_const',
    dest='template',
    const=METALINK3,
    help=argparse.SUPPRESS)

parser.add_argument('--meta4', '-4',
    action='store_const',
    dest='template',
    const=METALINK4,
    help=argparse.SUPPRESS)

parser.add_argument('--old-metalink', '--alternates-from', metavar='METALINK',
    type=pathlib.Path,
    help='load alternates from old metalink')

parser.add_argument('--alt-max-count', metavar='COUNT',
    type=int,
    help='maximum count of alternates, not including main file; 0 to disable'
        ' (default: %(default)d)')

parser.add_argument('--alt-max-age', metavar='SECONDS',
    type=int,
    help='maximum age of alternates, as seconds between main file and'
        ' alternate; 0 to disable (default: %(default)d)')

parser.set_defaults(template=METALINK3, base='.',
    alt_max_count=0, alt_max_age=2*24*3600)

def main(args=None):
    # pylint: disable=missing-docstring
    args = parser.parse_args(args)
    repomd = RepoMD(args.repomd)
    if args.old_metalink:
        repomd.load_alternates(args.old_metalink,
            max_count=args.alt_max_count, max_age=args.alt_max_age)

    urls = list(repomd.get_urls_for_mirrors(args.base, args.mirrors))
    assert urls, 'this file is not mirrored by any repo'

    sys.stdout.write(args.template.render(
        file=repomd,
        hashtypes=DEFAULT_HASHES,
        urls=urls,
        utcnow=datetime.datetime.utcnow(),
        generator='{}/{}'.format(__name__.split('.')[0], _version),
    ))
    sys.stdout.close()

if __name__ == '__main__':
    main()
