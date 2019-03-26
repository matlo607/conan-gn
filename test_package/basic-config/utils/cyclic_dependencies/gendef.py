#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__doc__ = ("Generate a module definition (.def) file from dumpbin's output run with the option"
           " '/LINKERMEMBER:2'. This option displays public symbols defined in a library.")

__version__ = '0.1'
__author__ = 'Matthieu Longo'


import argparse
from collections import namedtuple
import copy
import json
import logging
import os
import pprint
import re
import stat
import sys

try:
    import coloredlogs
    coloredlogs.DEFAULT_LOG_FORMAT = '[%(levelname)s] %(message)s'
    # If you don't want to see log messages from libraries, you can pass a
    # specific logger object to the install() function. In this case only log
    # messages originating from that logger will show up on the terminal.
    coloredlogs.install(level='DEBUG', logger=logging.getLogger())
except ImportError:
    pass


def parse_args():
    """
        Parse the script arguments
    """
    from argparse import ArgumentError

    def check_path(path):
        """
            Paths checker
        """
        if not os.path.exists(path):
            msg = "{path} does not exist".format(path=path)
            logging.error(msg)
            raise ValueError(msg)
        return path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dumpbin_outputs', metavar='DUMPBIN_OUTPUT', nargs='+',
                        type=check_path,
                        help="dumpbin's output run with the option '/LINKERMEMBER:2'")
    parser.add_argument('-n', "--dll", metavar='DLL_NAME', dest='dllname',
                        required=True,
                        help="Name of the DLL that will appear in the definition file")
    parser.add_argument('-o', '--output', metavar='OUTFILE',
                        required=False,
                        help="Definition file containing all the public symbols from dumpbin's outputs."
                             " Duplicated symbols are removed.")
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Print debug information')

    args = parser.parse_args()
    return args


class DefFileRenderer(object):

    @classmethod
    def render(cls, dllname, symbols):
        from io import StringIO
        output = StringIO()
        output.write("LIBRARY {library_name}\r\n".format(library_name=dllname))
        output.write("EXPORTS\r\n")
        for symbol in symbols:
            output.write("    {}\r\n".format(symbol))
        output.write("\r\n")
        content = output.getvalue()
        output.close()
        return content


class ScriptWritter(object):

     def __init__(self, dllname, symbols):
         self._dllname = dllname
         self._symbols = symbols

     def write(self, fd, renderer):
         fd.write(renderer.render(self._dllname, self._symbols))


class DumpbinOutputParser(object):

    __FILE_TYPE_MATCHER = re.compile(r"""File Type: (\w+([ \t]+\w+)*)$""")
    __SYMBOLS_OFFSET_MATCHER = re.compile(r"""Archive member name at (\d+)""")
    __N_SYMBOLS_MATCHER = re.compile(r"""[ \t]*(\d+) public symbols$""")
    __SYMBOL_MATCHER = re.compile(r"""[ \t]+\d+[ \t]+(\S+)$""")

    def __init__(self, fd):
        self._fd = fd
        self._file_type = None

    def valid_file_type(self):
        VALID_FILE_TYPES = { "LIBRARY" }
        line = self._fd.readline()
        while line:
            res = self.__FILE_TYPE_MATCHER.match(line)
            if res:
                self._file_type = res.group(1)
                logging.debug("file type: {}".format(self._file_type))
                if self._file_type in VALID_FILE_TYPES:
                    return True
                else:
                    return False
            line = self._fd.readline()
        return False

    def _get_symbols_offset(self):
        current_offset = self._fd.tell()
        line = self._fd.readline()
        while line:
            res = self.__SYMBOLS_OFFSET_MATCHER.match(line)
            if res:
                relative_offset = int(res.group(1))
                symbols_offset = current_offset + res.end() + relative_offset
                logging.debug("symbols offset: {}".format(symbols_offset))
                return symbols_offset
            else:
                current_offset = self._fd.tell()
            line = self._fd.readline()
        return None

    def _get_n_symbols(self):
        line = self._fd.readline()
        while line:
            res = self.__N_SYMBOLS_MATCHER.match(line)
            if res:
                n = int(res.group(1))
                logging.debug("{} symbols expected".format(n))
                return n
            line = self._fd.readline()
        return 0

    def _extract_symbol(self, line):
        res = self.__SYMBOL_MATCHER.match(line)
        return res.group(1) if res else None

    def extract_symbols(self):
        symbols = set()
        symbols_offset = self._get_symbols_offset()
        if symbols_offset is None:
            logging.warning("No symbol was found in this file.")
            return set()
        n = self._get_n_symbols()
        if n > 0:
            parsed = 0
            self._fd.seek(symbols_offset)
            for line in self._fd:
                symbol = self._extract_symbol(line)
                if symbol is None:
                    logging.warning("Unexpected end of symbols list ({}/{} founds)".format(parsed, n))
                    break
                logging.debug("\t{symbol}".format(symbol=symbol))
                symbols.add(symbol)
                parsed += 1
                if parsed >= n:
                    break
        return symbols


def run(args):
    def process_input(fd):
        parser = DumpbinOutputParser(fd)
        if not parser.valid_file_type():
            logging.error("Invalid file type")
            return None
        symbols = parser.extract_symbols()
        return symbols

    symbols = set()

    if len(args.dumpbin_outputs) == 0:
        file_symbols = process_input(sys.stdin)
        if file_symbols is not None:
            symbols = file_symbols
    else:
        for dumpbin_output in args.dumpbin_outputs:
            with open(dumpbin_output, 'r') as fd:
                file_symbols = process_input(fd)
                if file_symbols is not None:
                    symbols = symbols.union(file_symbols)

    renderer = DefFileRenderer()
    writter = ScriptWritter(args.dllname, symbols)
    if args.output is None:
        writter.write(sys.stdout, renderer)
    else:
        with open(args.output, 'w') as fd_out:
            writter.write(fd_out, renderer)
    return 0


if __name__ == '__main__':
    #try:
        args = parse_args()
        if args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Arguments:\n%s", pprint.pformat(vars(args), indent=2))
        sys.exit(run(args))
    #except Exception as e:
    #    logging.error(str(e))
    #    sys.exit(1)
