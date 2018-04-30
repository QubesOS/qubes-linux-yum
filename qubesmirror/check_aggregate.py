#!/usr/bin/env python3
#
#!/usr/bin/env python3
#
# qubesmirror -- a simple mirror manager for yum repos
# Copyright (C) 2018  Wojtek Porczyk <woju@invisiblethingslab.com>
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

'''Aggregator for checker'''

import argparse
import datetime
import json
import pathlib
import urllib.parse

parser = argparse.ArgumentParser()

parser.add_argument('paths', metavar='RESULT',
    type=pathlib.Path,
    nargs='+',
    help='path to result.json')

class Check:
    '''A point-in-time check against several mirrors'''
    # pylint: disable=too-few-public-methods
    def __init__(self, obj):
        self.path = obj['path']
        self.utcnow = datetime.datetime.strptime(obj['utcnow'],
            '%Y-%m-%dT%H:%M:%SZ')
        self.mirrors = obj['mirrors']

    def __lt__(self, other):
        return self.utcnow < other.utcnow

class ReportFormatter:
    '''Generate a report based on mirror checks'''
    def __init__(self, checks):
        self.checks = sorted(checks)
        mirrors = set()
        for check in self.checks:
            assert check.path == self.checks[0].path
            mirrors.update(check.mirrors)
        self.mirrors = sorted(mirrors, key=self._url_sort_key)

    @staticmethod
    def _url_sort_key(url):
        '''Used as key= argument for sorting :py:func:`urllib.parse.urlsplit`'''
        url = urllib.parse.urlsplit(url)
        if url.netloc.endswith('.qubes-os.org'):
            # sort this as first element
            return ()
        return (tuple(reversed(url.netloc.strip('.').split('.'))),
                url.scheme, url.path)

    def get_lines(self):
        '''Generate lines for printing'''
        yield '\n'.join('{:3d} {}'.format(i, mirror)
            for i, mirror in enumerate(self.mirrors))

        yield '{:20s}  {}'.format('TIMESTAMP',
            ' '.join('{!s:7s}'.format(i) for i in range(len(self.mirrors))))

        for check in self.checks:
            yield '{:%Y-%m-%d %H:%M:%SZ}  {}'.format(check.utcnow, ' '.join(
                self.format_cell(check.mirrors.get(mirror))[:7].rjust(7)
                    for mirror in self.mirrors))

    @staticmethod
    def format_cell(mirror):
        '''Format a single cell in table based on mirror's dict'''
        if mirror is None:
            return '-'

        if mirror.get('error') is not None:
            return 'ERROR'

        if mirror.get('status') is not None and not (
                200 <= mirror['status'] < 300):
            return '!{}'.format(mirror['status'])

        return mirror['sha256']


def main(args=None):
    # pylint: disable=missing-docstring
    args = parser.parse_args(args)
    report = ReportFormatter(Check(json.load(path.open()))
        for path in args.paths)
    for line in report.get_lines():
        print(line)

if __name__ == '__main__':
    main()
