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

'''Simple mirror manager for yum repos, as used in Qubes OS infra.'''

__version__ = '2.0'

import argparse
import hashlib
import operator
import pathlib
import posixpath
import sys

import lxml.etree

class Mirror(tuple):
    '''A representation of a mirror'''
    def __new__(cls, url, subdir='.'):
        return super().__new__(cls, (url, subdir))
    def __repr__(self):
        return '{}(url={!r}, subdir={!r})'.format(
            type(self).__name__, self.url, self.subdir)
    url = property(operator.itemgetter(0),
        doc='Base URL for the mirror')
    subdir = property(operator.itemgetter(1),
        doc='A subdirectory mirrored, or \'.\' if not a partial mirror')

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

class MirrorsAction(argparse.Action):
    '''Action which will load mirrors.list file'''
    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, 'mirrors', list(read_mirrors(pathlib.Path(values))))

def get_common_parser():
    # pylint: disable=missing-docstring
    parser = argparse.ArgumentParser()

    parser.add_argument('--base', '--cwd', '-b', metavar='PATH',
        type=pathlib.Path,
        help='base directory for repositories (default: %(default)r)')

    parser.add_argument('mirrors', metavar='MIRRORLIST',
        action=MirrorsAction,
        help='file to read the mirror list from')

    parser.add_argument('repomd', metavar='REPOMD',
        type=pathlib.Path,
        help='path to repomd.xml')

    parser.set_defaults(base='.')
    return parser
