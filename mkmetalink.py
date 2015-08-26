#!/usr/bin/env python2

#
# The Qubes OS Project, https://www.qubes-os.org/
#
# Copyright (C) 2015  Joanna Rutkowska <joanna@invisiblethingslab.com>
# Copyright (C) 2015  Wojtek Porczyk <woju@invisiblethingslab.com>
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


import argparse
import hashlib
import os
import posixpath
import sys
import time
import urllib #.parse #python3

import lxml.etree

DEFAULT_HASHES = [
    'md5',
    'sha1',
    'sha256',
    'sha512',
    'ripemd160',
]

DEFAULT_MIRRORS = [
    'http://ftp.qubes-os.org/repo/yum/',
    'http://mirrors.kernel.org/qubes/repo/yum/',
]

__version__ = '1.0'


class Metalink(object):
    def __init__(self, path):
        self.path = os.path.relpath(os.path.realpath(path))
        stat = os.stat(self.filename)

        self.root = lxml.etree.Element('metalink',
            nsmap={
                None: 'http://www.metalinker.org/',
                'mm0': 'http://fedorahosted.org/mirrormanager',
            },
            version='3.0',
            generator='mkmetalink/{}'.format(__version__))

        files = self._element('files')
        self.root.append(files)

        self.repomd = self._element('file', name='repomd.xml')
        files.append(self.repomd)

        self.add_timestamp()

        self.repomd.append(self._element('size',
            str(stat.st_size)))

        self.verification = self._element('verification')
        self.repomd.append(self.verification)

        self.resources = self._element('resources')
        self.repomd.append(self.resources)


    @staticmethod
    def _element(_tag, _text=None, **kwargs):
        element = lxml.etree.Element(_tag, **kwargs)
        if _text is not None:
            element.text = _text
        return element


    @property
    def filename(self):
        return os.path.join(self.path, 'repodata', 'repomd.xml')


    def add_timestamp(self):
        xml = lxml.etree.parse(self.filename)
        timestamp = max(int(e.text)
            for e in xml.xpath('/repomd:repomd/repomd:data/repomd:timestamp',
                namespaces={'repomd': 'http://linux.duke.edu/metadata/repo'}))
        self.repomd.append(self._element(
            '{http://fedorahosted.org/mirrormanager}timestamp',
            str(timestamp)))



    def add_hash(self, algo):
        h = hashlib.new(algo)
        f = open(self.filename, 'rb')

        while True:
            data = f.read(1024)
            if not data:
                break
            h.update(data)

        f.close()

        element = lxml.etree.Element('hash', type=algo)
        element.text = h.hexdigest()
        self.verification.append(element)

        return element


    def add_resource(self, mirror):
#       scheme = urllib.parse.urlsplit(mirror)[0] #python3
        scheme = urllib.splittype(mirror)[0] #python2
        element = lxml.etree.Element('url', protocol=scheme, type=scheme)
        element.text = posixpath.join(mirror, self.filename)
        self.resources.append(element)

        return element


    def write(self, stream):
        return lxml.etree.ElementTree(self.root).write(
            stream, encoding='utf-8', pretty_print=True)


    def save(self):
        self.write(open(os.path.join(self.path, 'metalink'), 'wb'))


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter,
    epilog='default mirrors: {}\ndefault hashes:  {}'.format(
        ', '.join(DEFAULT_MIRRORS), ', '.join(DEFAULT_HASHES)))

parser.add_argument('--base', '--cwd', '-b', metavar='PATH',
    help='base directory for repositories (default: %(default)r)')

parser.add_argument('--hash', '-H', metavar='ALGO',
    action='append',
    help='hash files with this algorithm; can be repeated')

parser.add_argument('--mirrorlist', '-M', metavar='FILE',
    help='mirror file containing list of mirrors')

parser.add_argument('repo', metavar='REPOSITORY',
    help='path to repository relative to --base,\n'
        'for example r3.0/current-testing/dom0/fc20')

parser.set_defaults(base='.')


def main():
    args = parser.parse_args()

    os.chdir(args.base)
    metalink = Metalink(args.repo)

    hashes = args.hash or DEFAULT_HASHES
    for algo in hashes:
        metalink.add_hash(algo)

    mirrors = open(args.mirrorlist).read().strip().split() \
        if args.mirrorlist is not None \
        else DEFAULT_MIRRORS
    for mirror in mirrors:
        metalink.add_resource(mirror)

    metalink.save()


if __name__ == '__main__':
    main()


# vim: ts=4 sts=4 sw=4 et
