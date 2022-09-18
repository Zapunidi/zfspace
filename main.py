import os

class SnapshotSpace:
    sizes_test = {100, 917020001, 2950810867664, 1417432010192, 63699569296, 31936161312, 180680896, 180680896}
    term_format = dict(PURPLE='\033[95m', CYAN='\033[96m', DARKCYAN='\033[36m', BLUE='\033[94m',
                       GREEN='\033[92m', YELLOW='\033[93m', RED='\033[91m', BOLD='\033[1m',
                       UNDERLINE='\033[4m', END='\033[0m')

    def __init__(self):
        self.term_columns, self.term_lines = os.get_terminal_size()

    def _size2human(self, size):
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

    def _print_line(self, sizes):
        # Calculate fractional space for strings including len + 1 separators
        frac_size = (self.term_columns - len(sizes) - 1) / len(sizes)  # possibly non integer length
        pos = 0
        for size in sizes:
            pos += frac_size
            length = int(pos)
            print('|', end='')
            self._print_used(size, length - 1)
            pos -= length
        print('|')  # New line afterwards

    def _print_used(self, used, str_length):
        len = '{:d}'.format(str_length)
        print('{:^12s} {}'.format(self._size2human(used), str_length), end='')

    def test(self):
        for size in self.sizes_test:
            print(self._size2human(size))
        print('columns = {}, lines = {}'.format(self.term_columns, self.term_lines))
        print(self.term_format['BOLD'] + 'Hello World !' + self.term_format['END'])


def main():
    ss = SnapshotSpace()
    ss.test()
    ss._print_line(ss.sizes_test)


if __name__ == '__main__':
    main()
