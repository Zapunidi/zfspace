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
import math


term_format = dict(PURPLE='\033[95m', CYAN='\033[96m', DARKCYAN='\033[36m', BLUE='\033[94m',
                   GREEN='\033[92m', YELLOW='\033[93m', RED='\033[91m', BOLD='\033[1m',
                   UNDERLINE='\033[4m', END='\033[0m')


def size2human(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "kiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return '{:.4} {}'.format(s, size_name[i])


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
        command = 'zfs list -H -d 1 -t snapshot -s creation -o name {}'.format(dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\n')[:-1]  # Take all strings of ZFS snapshot listing except last one
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
        # The occupied space we have in the matrix shows how much space will be freed if we delete the combination
        # While this might be useful to make a decision, this does not show used space hierarchy
        # Let's calculate the space occupied by snapshots combination and not by its subsets

        # Now define a helper function for triange substraction
        def substract_children(matrix, startx, starty):
            for x in range(startx):
                for y in range(starty, starty + startx - x + 1):
                    matrix[startx][starty] -= matrix[x][y]
        # Then row by row we substract space occupied by subsets
        # This is the correct way
        for i in range(1, len(snapshot_list)):
            for j, _ in enumerate(snapshot_list):
                if j < len(snapshot_list) - i:
                    substract_children(used_matrix, i, j)
        # Now we can get the whole snapshots occupied space by summing every matrix cell
        return used_matrix

    def get_dataset_summary(self, dataset_name):
        if dataset_name not in self.zfs_datasets:
            raise ValueError('There is no dataset {} in the system.\n'
                             'The following datasets were found by "zfs list" command: {}'
                             ''.format(dataset_name, self.zfs_datasets))
        command = 'zfs list -p -o space {}'.format(dataset_name)
        stream = os.popen(command)
        data = list(filter(None, stream.read().split('\n')[-2].split(' ')))  # Get second string and split it by spaces
        print(data)


class SnapshotSpace:
    def __init__(self, dataset_name):
        self.term_columns, self.term_lines = os.get_terminal_size()
        self.zb = ZfsBridge()
        self.snapshot_names = self.zb.get_snapshot_names(dataset_name)
        self.snapshot_size_matrix = self.zb.get_snapshots_space(dataset_name, self.snapshot_names)

    def print_used(self):
        for i in reversed(range(1, len(self.snapshot_names))):
            self._print_line(self.snapshot_size_matrix[i][:-i])
        self._print_line(self.snapshot_size_matrix[0])  # Last line falls out of general rule
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
        max_split = len(self.snapshot_names)
        start, end = self._split_terminal_line(len(sizes),
                                               int((max_split - len(sizes)) * self.term_columns / max_split / 2))
        print(' ' * (start[0] - 1) + '|', end='')  # shifting for padding
        for i, size in enumerate(sizes):
            self._print_in_line(size2human(size), end[i] - start[i])
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


def main():
    if len(sys.argv) != 2:
        sys.exit("Usage: {} <datasetname>".format(sys.argv[0]))
    dataset_name = sys.argv[1]

    # Preparing classes
    ss = SnapshotSpace(dataset_name)
    zb = ZfsBridge()

    # Printing user intro
    print('Analyzing ' + term_format['BOLD'] + dataset_name + term_format['END'] + ' ZFS dataset.')
    zb.get_dataset_summary(dataset_name)
    ss.print_used()
