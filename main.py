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
        for string in output:
            self.zfs_datasets.append(string.split(' ')[0])

    @staticmethod
    def strip_filesystem_name(snapshot_name):
        """Given the name of a snapshot, strip the filesystem part.

        We require (and check) that the snapshot name contains a single
        '@' separating filesystem name from the 'snapshot' part of the name.
        """
        assert snapshot_name.count('@') == 1
        return snapshot_name.split('@')[1]

    def get_snapshot_names(self, dataset_name):
        if dataset_name not in self.zfs_datasets:
            raise ValueError('There is no dataset {} in the system.\n'
                             'The following datasets were found by "zfs list" command: {}'
                             ''.format(dataset_name, self.zfs_datasets))
        command = 'zfs list -r -t snapshot -s creation -o name {}'.format(dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\n')[1:-1]  # Take all strings of ZFS snapshot listing except first and last one
        return list(map(self.strip_filesystem_name, output))

    @ staticmethod
    def _get_snapshot_range_space(dataset, first_snap, last_snap):
        command = 'zfs destroy -nvp {}@{}%{}'.format(dataset, first_snap, last_snap)
        stream = os.popen(command)
        return stream.read().split('\n')[-2].split('\t')[-1]  # Take the second part of the last line

    def get_snapshots_space(self, dataset_name, snapshot_list):
        if dataset_name not in self.zfs_datasets:
            raise ValueError('There is no dataset {} in the system.\n'
                             'The following datasets were found by "zfs list" command: {}'
                             ''.format(dataset_name, self.zfs_datasets))
        used_matrix = [[0 for _ in range(len(snapshot_list))] for _ in range(len(snapshot_list))]
        for end, end_name in enumerate(snapshot_list):
            for start, start_name in enumerate(snapshot_list):
                if start <= end:
                    used_matrix[end - start][start] = \
                        int(self._get_snapshot_range_space(dataset_name, start_name, end_name))
        print(used_matrix)
        return used_matrix


class SnapshotSpace:
    sizes_test = {100, 917020001, 2950810867664, 1417432010192, 63699569296, 31936161312, 180680896, 180680897}
    term_format = dict(PURPLE='\033[95m', CYAN='\033[96m', DARKCYAN='\033[36m', BLUE='\033[94m',
                       GREEN='\033[92m', YELLOW='\033[93m', RED='\033[91m', BOLD='\033[1m',
                       UNDERLINE='\033[4m', END='\033[0m')

    def __init__(self, dataset_name):
        self.term_columns, self.term_lines = os.get_terminal_size()
        self.zb = ZfsBridge()
        self.snapshot_names = self.zb.get_snapshot_names(dataset_name)
        self.snapshot_size_matrix = self.zb.get_snapshots_space(dataset_name, self.snapshot_names)

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
        for i in reversed(range(1, len(self.snapshot_names))):
            self._print_line(self.snapshot_size_matrix[i][:-i])
        self._print_names()

    def _split_terminal_line(self, slices, padding=0):
        # Calculate fractional space for strings considering (slices + 1) separators and padding
        start_pos = list()
        end_pos = list()
        frac_size = (self.term_columns - slices - 1 - padding * 2) / slices  # possibly non integer length
        pos = 1 + padding
        for _ in range(slices):
            start_pos.append(int(pos))
            pos += frac_size
            end_pos.append(int(pos))
            pos += 1  # space for separator
        return start_pos, end_pos

    def _print_line(self, sizes):
        start, end = self._split_terminal_line(len(sizes))
        print(' ' * (start[0] - 1) + '|', end='')  # shifting for padding
        for i, size in enumerate(sizes):
            self._print_in_line(self._size2human(size), end[i] - start[i])
            print('|', end='')
        print('')  # New line afterwards

    def _print_names(self):
        start, end = self._split_terminal_line(len(self.snapshot_names))
        for i, name in enumerate(self.snapshot_names):
            print('|', end='')
            self._print_in_line(name, end[i] - start[i])
        print('|')  # New line afterwards

    @staticmethod
    def _print_in_line(string, str_length):
        len_format = '{:^' + '{:d}'.format(str_length) + 's}'  # Prepare format string with desired width
        print(len_format.format(string), end='')

    def test(self):
        print(self.term_format['BOLD'] + 'Hello World !' + self.term_format['END'])


def main(dataset_name):
    # Preparing classes
    ss = SnapshotSpace(dataset_name)

    # Printing user intro
    print('Analyzing {} ZFS dataset.'.format(dataset_name))
    ss.test()
    ss.print_used()


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        sys.exit("Usage: {} <datasetname>".format(sys.argv[0]))
