#!/usr/bin/env python3
""" Usage: zfspace <dataset name>

Console tool to find occupied pool space in ZFS on Linux.

The main purpose is to visualize missing space that is hidden in snapshots.
ZFS only shows space occupied by a snapshot's unique data and doesn't
show space occupied by data referenced in 2+ snapshots. Therefore searching
for missing space can be troublesome. zfspace helps with that and tries to be
explanatory for inexperienced users.
"""

import os
import sys
import math
import difflib
import argparse


term_format = dict(PURPLE='\033[95m', CYAN='\033[96m', DARKCYAN='\033[36m', BLUE='\033[94m',
                   GREEN='\033[92m', YELLOW='\033[93m', RED='\033[91m', BOLD='\033[1m',
                   UNDERLINE='\033[4m', WHITEBOLD='\033[1;37m', END='\033[0m')


def size2human(size_bytes: int):
    """Convert size in bytes into human readable format like MiB or GiB.
    Sizes up to YiB (>10^24) are supported. The result is rounded to 2-4 meaningful digits.

    :param int size_bytes: The bytes number that needs to be put into human readable form
    :return: Short string representing size (14.1 GiB for example)
    :rtype: str
    """
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "kiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB")
    order = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, order)
    digits = int(math.floor(math.log(size_bytes / p, 10)))  # Calculate meaningful digits to keep length in 4 characters
    if digits > 1:  # Only integer output is suitable for values over 100.
        s = int(round(size_bytes / p))
        return '{} {}'.format(s, size_name[order])
    else:  # Limit accuracy to 1 or 2 fractional decimals to get representations 1.23 and 12.3 and not 12.34
        s = round(size_bytes / p, 2 - digits)
        return '{:.4} {}'.format(s, size_name[order])


def split_terminal_line(term_columns, slices=0, fractions_list=list(), padding=0):
    # Convert slices into fractions_list
    if len(fractions_list) == 0:
        if slices is 0:
            raise TypeError('At least one parameter must be set. '
                            'Either slices > 0 or fractions_list must be a not empty list.')
        else:
            fractions_list = [1/slices] * slices
    else:
        slices = len(fractions_list)

    # Normalize fractions_list
    fractions_list = [float(i) / sum(fractions_list) for i in fractions_list]

    # Calculate fractional space for strings considering (slices + 1) separators and padding
    start_pos = list()
    end_pos = list()
    writable_columns = (term_columns - slices - 1 - padding * 2)
    pos = 1 + padding
    for frac in fractions_list:
        start_pos.append(int(pos))
        pos += writable_columns * frac
        end_pos.append(int(pos))
        pos += 1  # space for separator
    return start_pos, end_pos


def print_in_line(string, str_length):
    """Prints centered output, considering that console cursor is in the beginning of the span to print.
    Prints . or nothing if there is not enough space to print wrole string

    :param string: String to print
    :param int str_length: Integer number of symbols to fill with string
    :return: None
    """
    if len(string) > str_length:
        string = '.' * str_length
    if str_length == 0:
        return
    len_format = '{:^' + '{:d}'.format(str_length) + 's}'  # Prepare format string with desired width
    print(len_format.format(string), end='')


class DivBar:
    """
    An object to draw console visual representations of parts as bars forming a whole
    """
    def __init__(self):
        self.term_columns, self.term_lines = os.get_terminal_size()

    def print_dict(self, names_list):
        """ Print a bar in terminal divided into segments. It helps to visualize the differences in sizes.

        :param names_list: a list of tuples consisting of a name of a segment and its integer size
        :return: None
        """
        names, sizes = zip(*names_list)
        start, end = split_terminal_line(self.term_columns, fractions_list=sizes)
        for i, name in enumerate(names):
            print('|', end='')
            print_in_line(name + ' ' + size2human(sizes[i]), end[i] - start[i])
        print('|')  # New line afterwards


class ZfsBridge:
    zfs_path = '/sbin/zfs'

    def __init__(self):
        # Check whether zfs is present in the system
        if not os.path.isfile('/sbin/zfs'):
            raise FileNotFoundError(
                '{} is not found on your computer. Is ZFS-on-Linux installed?'.format(self.zfs_path))
        # Check and store existing ZFS datasets to be able to explain the user's input errors
        stream = os.popen('{} list'.format(self.zfs_path))
        output = stream.read().split('\n')[1:-1]  # Take all strings of ZFS listing except first and last one
        self.zfs_datasets = list()
        for string in output:
            self.zfs_datasets.append(string.split(' ')[0])

    @staticmethod
    def strip_filesystem_name(snapshot_name: str):
        """Given the name of a snapshot, strip the filesystem part.

        We require (and check) that the snapshot name contains a single
        '@' separating filesystem name from the 'snapshot' part of the name.
        :param str snapshot_name: A standard single snapshot name with trailing filesystem and @ symbol
        :return: The name of the snapshot that goes after @ symbol
        :rtype: str
        """
        assert snapshot_name.count('@') == 1
        return snapshot_name.split('@')[1]

    def _check_dataset_name(self, dataset_name):
        if dataset_name not in self.zfs_datasets:
            candidate_list = difflib.get_close_matches(dataset_name, self.zfs_datasets, n=1)
            if len(candidate_list) == 1:
                suggest_str = '\nDid you mean using "{}" instead?'.format(candidate_list[0])
            else:
                suggest_str = ''
            raise ValueError('There is no dataset "{}" in the system.{}'.format(dataset_name, suggest_str))

    def get_filesystem_mountpoint(self, dataset_name):
        self._check_dataset_name(dataset_name)
        command = '{} get -Hp mountpoint {}'.format(self.zfs_path, dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\t')[2]
        return output

    def get_filesystem_refreservation(self, dataset_name):
        self._check_dataset_name(dataset_name)
        command = '{} get -Hp refreservation {}'.format(self.zfs_path, dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\t')[2]
        return int(output)

    def get_children_summary(self, dataset_name):
        self._check_dataset_name(dataset_name)
        command = '{} list -d 1 -p -S used -o space {}'.format(self.zfs_path, dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\n')[:-1]  # Get all lines except the last one, that is empty
        names = list(filter(None, output[0].split(' ')))
        children = list()
        for child in output[1:]:
            item = list(filter(None, child.split(' ')))
            if item[0] == dataset_name:  # Filter out the parent
                continue
            data = [item[0]] + list(map(int, item[1:]))  # Convert to integers all but name of the dataset
            children.append(list(zip(names, data)))
        return children

    def get_snapshot_names(self, dataset_name):
        self._check_dataset_name(dataset_name)
        command = '{} list -H -d 1 -t snapshot -s creation -o name {}'.format(self.zfs_path, dataset_name)
        stream = os.popen(command)
        output = stream.read().split('\n')[:-1]  # Take all strings of ZFS snapshot listing except last one
        return list(map(self.strip_filesystem_name, output))

    def _get_snapshot_range_space(self, dataset, first_snap, last_snap):
        command = '{} destroy -nvp {}@{}%{}'.format(self.zfs_path, dataset, first_snap, last_snap)
        stream = os.popen(command)
        return stream.read().split('\n')[-2].split('\t')[-1]  # Take the second part of the last line

    def get_snapshots_space(self, dataset_name, snapshot_list):
        self._check_dataset_name(dataset_name)
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
        self._check_dataset_name(dataset_name)
        command = '{} list -p -o space {}'.format(self.zfs_path, dataset_name)
        stream = os.popen(command)
        string_list = stream.read().split('\n')[0:2]  # Get names and data strings
        # Split it by spaces and remove empty strings.
        data = list(filter(None, string_list[1].split(' ')))
        names = list(filter(None, string_list[0].split(' ')))
        data = [data[0]] + list(map(int, data[1:]))  # Convert to integers all but name
        return list(zip(names, data))


class SnapshotSpace:
    zfs_max_snapshots = 30

    def __init__(self, dataset_name):
        self.term_columns, self.term_lines = os.get_terminal_size()
        self.zb = ZfsBridge()
        self.snapshot_names = self.zb.get_snapshot_names(dataset_name)
        if len(self.snapshot_names) >= self.zfs_max_snapshots:
            raise ValueError('You have more than {} snapshots in {}. It is too many to show in console.'
                             .format(len(self.snapshot_names), dataset_name))
        self.snapshot_size_matrix = self.zb.get_snapshots_space(dataset_name, self.snapshot_names)

    def print_used(self):
        for i in reversed(range(1, len(self.snapshot_names))):
            self._print_line(self.snapshot_size_matrix[i][:-i])
        self._print_line(self.snapshot_size_matrix[0])  # Last line falls out of general rule
        self._print_names()

    def _print_line(self, sizes):
        max_split = len(self.snapshot_names)
        start, end = split_terminal_line(self.term_columns, slices=len(sizes),
                                         padding=int((max_split - len(sizes)) * self.term_columns / max_split / 2))
        print(' ' * (start[0] - 1) + '|', end='')  # shifting for padding
        for i, size in enumerate(sizes):
            print_in_line(size2human(size), end[i] - start[i])
            print('|', end='')
        print('')  # New line afterwards

    def _print_names(self):
        start, end = split_terminal_line(self.term_columns, slices=len(self.snapshot_names))
        for i, name in enumerate(self.snapshot_names):
            print('|', end='')
            print_in_line(name, end[i] - start[i])
        print('|')  # New line afterwards


def deep_analysis(zb: ZfsBridge, dataset_name, name, size):
    global filter_level

    def hello_helper(section_name, size_bytes, text):
        print(term_format['WHITEBOLD'] + section_name + term_format['END'] + ' occupy ' + term_format['CYAN'] +
              size2human(size_bytes) + term_format['END'] + '. ' + text)

    if name == 'USEDSNAP':
        hello_helper('Snapshots', size, 'This space consists of data unique for individual snapshots and data stored in'
                     ' snapshots combinations. Therefore we will use pyramid representation:')
        ss = SnapshotSpace(dataset_name)
        ss.print_used()
        print('Recommendation to remove the following snapshots: TODO')

    elif name == 'USEDDS':
        hello_helper('Files in {}'.format(zb.get_filesystem_mountpoint(dataset_name)), size,
                     'Recommendation to delete files: TODO')

    elif name == 'USEDREFRESERV':
        hello_helper('Refreservation option', size,
                     'Current refreservation value is {}. '.format(
                         size2human(zb.get_filesystem_refreservation(dataset_name))
                     ) + 'Remove it with "{} set refreservation=0 {}".'.format(zb.zfs_path, dataset_name))

    elif name == 'USEDCHILD':
        hello_helper('Children ZFS filesystems', size, 'The following children may be considered to be cleaned:')
        dv = DivBar()
        used_all_children = zb.get_dataset_summary(dataset_name)[6][1]
        part_count = 0
        for child in zb.get_children_summary(dataset_name):
            part_count += child[2][1] / used_all_children  # Normalized sum
            print(term_format['BOLD'] + str(child[0][1]) + term_format['END'] +
                  term_format['CYAN'] + ' {}'.format(size2human(child[2][1]) + term_format['END'] + ' of ' +
                  term_format['CYAN'] + '{}'.format(size2human(used_all_children)) + term_format['END'] +
                  ' ({:.3}%). '.format(round(100 * child[2][1] / used_all_children, 1)) +
                  'Run "zfspace {}" to make a more detailed analysis:'.format(child[0][1])))
            dv.print_dict(child[3:])
            if part_count >= filter_level:
                break

    else:
        raise ValueError('Unknown ZFS {} space user: {}'.format(dataset_name, name))


def get_my_version():
    with open(os.path.join(os.path.dirname(__file__), '../../pyproject.toml')) as fp:
        for line in fp:
            if line.startswith('version'):
                return 'Version' + line.split('=')[1]
        else:
            raise RuntimeError('Unable to find own __version__ string')


def main():
    parser = argparse.ArgumentParser(description='analyse space occupied by a ZFS filesystem.')
    parser.add_argument('-V', '--version', action='version', version=get_my_version())
    parser.add_argument('-f', '--filter', type=float,
                        help='Threshold in range [0,1] to filter out all less significant parts on analysis.',
                        default=0.632)
    parser.add_argument('dataset_name', type=str, help='a ZFS dataset name for analysis.')

    args = parser.parse_args()
    if args.filter > 1 or args.filter < 0:
        raise ValueError('The filter cannot be out of [0,1] range.')
    global filter_level
    filter_level = 1 - args.filter

    # Initializing ZFS helper class
    zb = None  # Fix warnings about possible usage before initialization
    try:
        zb = ZfsBridge()
    except Exception as err:
        print(err)
        exit()

    # Starting with dataset analysis
    summary = zb.get_dataset_summary(args.dataset_name)

    # Printing user intro
    print('Analyzing ' + term_format['WHITEBOLD'] + args.dataset_name + term_format['END'] + ' ZFS dataset. '
          'Total used space is ' + term_format['CYAN'] + size2human(summary[1][1]) + term_format['END'] + '. '
          'It is divided in the following way:')
    dv = DivBar()
    dv.print_dict(summary[3:])

    # Find the most important parts in summary according to filter level
    summary_sorted = sorted(summary[3:], key=lambda x: -x[1])
    part_count = 0
    for item in summary_sorted:
        part_count += item[1] / summary[2][1]  # Normalized sum
        try:
            print('')
            deep_analysis(zb, args.dataset_name, *item)  # Analyze each part individually
        except Exception as err:
            print(err)
            raise
        if part_count >= filter_level:
            break

main()