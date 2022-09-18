#!/usr/bin/env python3
""" Usage: zfspace <pool or dataset name>

Tool to analyze missing disk space by ZFS

The main purpose is to visualize missing space that is hidden in snapshots.
ZFS only shows space occupied by a snapshot's unique data and doesn't
show space occupied by data referenced in 2+ snapshots. Therefore searching
for missing space can be troublesome. zfspace helps with that and tries to be
explanatory for inexperienced users.
"""

import os
import sys


class ZfsBridge:
    def __init__(self):
        # Check and store existing ZFS datasets to be able to explain the user his input errors
        stream = os.popen('zfs list')
        output = stream.read().split('\n')[1:-1]  # Take all strings of ZFS listing except first and last one
        self.zfs_datasets = list()
        for str in output:
            self.zfs_datasets.append(str.split(' ')[0])

    @staticmethod
    def strip_filesystem_name(snapshot_name):
        """Given the name of a snapshot, strip the filesystem part.

        We require (and check) that the snapshot name contains a single
        '@' separating filesystem name from the 'snapshot' part of the name.
        """
        assert snapshot_name.count("@") == 1
        return snapshot_name.split("@")[1]

    def get_snapshots(self, dataset_name):
        if dataset_name not in self.zfs_datasets:
            raise ValueError('There is no dataset {} in the system.\n'
                             'The following datasets were found by "zfs list" command: {}'
                             ''.format(dataset_name, self.zfs_datasets))
        command = 'zfs list -r -t snapshot -s creation -o name {}'.format(dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\n')[1:-1]  # Take all strings of ZFS snapshot listing except first and last one
        return list(map(self.strip_filesystem_name, output))


class SnapshotSpace:
    sizes_test = {100, 917020001, 2950810867664, 1417432010192, 63699569296, 31936161312, 180680896, 180680897}
    term_format = dict(PURPLE='\033[95m', CYAN='\033[96m', DARKCYAN='\033[36m', BLUE='\033[94m',
                       GREEN='\033[92m', YELLOW='\033[93m', RED='\033[91m', BOLD='\033[1m',
                       UNDERLINE='\033[4m', END='\033[0m')

    def __init__(self):
        self.term_columns, self.term_lines = os.get_terminal_size()

    @staticmethod
    def _size2human(size):
        size_format = '{:.4}'

        if size < 0:
            raise ValueError('Snapshot size cannot be negative')
        if size < 1000:
            return ('{:5d}' + ' B').format(size)
        size /= 1024  # convert to kibibytes
        if size < 1000:
            return (size_format + ' KiB').format(size)
        size /= 1024  # convert to mebibytes
        if size < 1000:
            return (size_format + ' MiB').format(size)
        size /= 1024  # convert to gibibytes
        if size < 1000:
            return (size_format + ' GiB').format(size)
        size /= 1024  # convert to tebibytes
        if size < 1000:
            return (size_format + ' TiB').format(size)
        size /= 1024  # convert to pebibytes
        if size < 1000:
            return (size_format + ' PiB').format(size)
        else:
            raise ValueError('Did not expect snapshot size to exceed 1000 pebibytes')

    def print_used(self):
        self._print_line(self.sizes_test)

    def _print_line(self, sizes):
        # Calculate fractional space for strings including len + 1 separators
        frac_size = (self.term_columns - len(sizes) - 1) / len(sizes)  # possibly non integer length
        pos = 0
        for size in sizes:
            pos += frac_size
            length = int(pos)
            print('|', end='')
            self._print_used(size, length)
            pos -= length
        print('|')  # New line afterwards

    def _print_used(self, used, str_length):
        len_format = '{:^' + '{:d}'.format(str_length) + 's}'  # Prepare format string with desired width
        print(len_format.format(self._size2human(used)), end='')

    def test(self):
        print(self.term_format['BOLD'] + 'Hello World !' + self.term_format['END'])


def main(dataset_name):
    # Preparing classes
    ss = SnapshotSpace()
    zb = ZfsBridge()

    # Initializing with user input
    snapshot_list = zb.get_snapshots(dataset_name)

    # Printing user intro
    print('Analyzing {} ZFS dataset.'.format(dataset_name))
    ss.test()
    ss.print_used()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit("Usage: {} <datasetname>".format(sys.argv[0]))
