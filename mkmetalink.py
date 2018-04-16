#!/usr/bin/env python3
#
# mkmetalink.py -- generate simple metalink for yum repo
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

'''Simple generator of metalinks for yum repos, as used in Qubes OS infra.'''

__version__ = '2.0'

import argparse
import datetime
import hashlib
import operator
import pathlib
import posixpath
import sys

import jinja2
import lxml.etree

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
            <resources>
            {%- for url in urls %}
                <url>{{ url }}</url>
            {%- endfor %}
            </resources>
            <verification>
            {%- for hashtype in hashtypes %}
                <hash type="{{ hashtype }}">{{ file.get_hash(hashtype) }}</hash>
            {%- endfor %}
            </verification>
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
            {%- for url in urls %}
            <url>{{ url }}</url>
            {%- endfor %}
            {%- for hashtype in hashtypes %}
            <hash type="{{ hashtype }}">{{ file.get_hash(hashtype) }}</hash>
            {%- endfor %}
        </file>
    </files>
</metalink>
''')

parser = argparse.ArgumentParser()

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

parser.add_argument('--base', '--cwd', '-b', metavar='PATH',
    type=pathlib.Path,
    help='base directory for repositories (default: %(default)r)')

parser.add_argument('mirrors', metavar='MIRRORLIST',
    type=pathlib.Path,
    help='file to read the mirror list from')

parser.add_argument('repomd', metavar='REPOMD',
    type=pathlib.Path,
    help='paths to repomd.xmls to generate metalink for')

parser.set_defaults(template=METALINK3, base='.')

class RepoMD:
    '''A representation of repomd.xml file'''
    def __init__(self, path):
        self.path = path
        self.stat = self.path.stat()
        assert self.stat.st_size < 1e7, 'memory protection safeguard'
        # the assert is because we read the file into memory:
        self.contents = self.path.read_bytes()
        self.timestamp = self._get_timestamp()

    def _get_timestamp(self):
        xml = lxml.etree.XML(self.contents)
        return max(int(e.text)
            for e in xml.xpath('/repomd:repomd/repomd:data/repomd:timestamp',
                namespaces={'repomd': 'http://linux.duke.edu/metadata/repo'}))

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

class Mirror(tuple):
    def __new__(cls, url, subdir='.'):
        return super().__new__(cls, (url, subdir))
    def __repr__(self):
        return '{}(url={!r}, subdir={!r})'.format(
            type(self).__name__, self.url, self.subdir)
    url = property(operator.itemgetter(0))
    subdir = property(operator.itemgetter(1))

def read_mirrors(path):
    '''Read mirror file

    Format:
        - one mirror URL per line
        - after whitespace, optional subdirectory
            (if it does not mirror whole ``--base``)
        - empty and ``#`` lines are ignored
    '''
    with open(str(path)) as file:
        for line in file:
            line = line.strip()
            if not line or line[0] == '#':
                continue
            yield Mirror(*line.split())

def main(args=None):
    args = parser.parse_args(args)
    repomd = RepoMD(args.repomd)
    urls = list(
        repomd.get_urls_for_mirrors(args.base, read_mirrors(args.mirrors)))
    assert urls, 'this file is not mirrored by any repo'

    sys.stdout.write(args.template.render(
        file=repomd,
        hashtypes=DEFAULT_HASHES,
        urls=urls,
        utcnow=datetime.datetime.utcnow(),
        generator='mkmetalink/{}'.format(__version__),
    ))
    sys.stdout.close()

if __name__ == '__main__':
    main()
