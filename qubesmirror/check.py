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

'''Checker for mirrors to measure delay in syncing'''

import asyncio
import datetime
import hashlib
import json
import posixpath
import sys

import aiohttp

from . import get_common_parser

parser = get_common_parser()

class MirrorChecker:
    '''Checker for single mirror'''
    def __init__(self, path, base, mirror):
        self.mirror = mirror
        self.url = posixpath.join(mirror.url,
            str(path.relative_to(base / mirror.subdir)))

        self.sha256 = None
        self.status = None
        self.error = None
        self.history = None

    async def check(self, session):
        '''Execute the checker

        :param aiohttp.ClientSession session: aiohttp session
        '''
        try:
            digest = hashlib.sha256()
            async with session.get(self.url) as response:
                self.history = response.history
                self.status = response.status
                try:
                    response.raise_for_status()
                except aiohttp.ClientResponseError:
                    return
                while True:
                    chunk = await response.content.read(4096)
                    if not chunk:
                        self.sha256 = digest.hexdigest()
                        return
                    digest.update(chunk)
        except Exception as err: # pylint: disable=broad-except
            self.error = str(err)

    def asdict(self):
        # pylint: disable=missing-docstring
        return {'status': self.status, 'history': self.history,
                'sha256': self.sha256, 'error': self.error}

async def main(args=None):
    # pylint: disable=missing-docstring
    args = parser.parse_args(args)
    checkers = [MirrorChecker(args.repomd, args.base, mirror)
        for mirror in args.mirrors]
    utcnow = datetime.datetime.utcnow()

    async with aiohttp.ClientSession() as session:
        futures = []
        for checker in checkers:
            try:
                futures.append(checker.check(session))
            except ValueError:  # raised by Path.relative_to()
                sys.stderr.write('file {} not mirrored in {}\n'.format(
                    args.repomd, checker.url))
        await asyncio.gather(*futures)

    json.dump({
            'utcnow': utcnow.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'path': str(args.repomd),
            'mirrors': {checker.mirror.url: checker.asdict()
                for checker in checkers}
        }, sys.stdout, indent=4, sort_keys=True)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
