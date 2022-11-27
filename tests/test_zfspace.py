from unittest import TestCase
import os
from src.zfspace.zfspace import size2human, shorten_names


os.chdir(os.path.dirname(__file__) + '/..')


class TestZfspace(TestCase):
    def test_size2human(self):
        self.assertTrue(size2human(123) == '123 B')
        self.assertTrue(size2human(1_234) == '1.21 kiB')
        self.assertTrue(size2human(1_001) == '1001 B')
        self.assertTrue(size2human(1_002_000) == '979 kiB')
        self.assertTrue(size2human(2_000_000_000) == '1.86 GiB')
        self.assertTrue(size2human(2_000_000_000_000) == '1.82 TiB')
        self.assertTrue(size2human(2_000_000_000_000_000) == '1.78 PiB')
        self.assertTrue(size2human(1_150_000_000_000_000_000) == '1021 PiB')
        self.assertTrue(size2human(2_000_000_000_000_000_000_000) == '1.69 ZiB')

        try:
            size2human(2_000_000_000_000_000_000_000, fmt='bad')
        except ValueError:
            pass

        self.assertTrue(size2human(123, fmt='short') == '123B')
        self.assertTrue(size2human(1_234, fmt='short') == '1k')
        self.assertTrue(size2human(1_001, fmt='short') == '1001B')
        self.assertTrue(size2human(1_002_000, fmt='short') == '979k')
        self.assertTrue(size2human(2_000_000_000, fmt='short') == '2G')
        self.assertTrue(size2human(2_000_000_000_000, fmt='short') == '2T')
        self.assertTrue(size2human(2_000_000_000_000_000, fmt='short') == '2P')
        self.assertTrue(size2human(1_150_000_000_000_000_000, fmt='short') == '1021P')
        self.assertTrue(size2human(2_000_000_000_000_000_000_000, fmt='short') == '2Z')

    def test_shorten_names(self):
        names = ['zfs_1', 'zfs_2', 'zfs_backup']
        shortn = shorten_names(names)
        self.assertTrue(shortn[0] == '...1')
        self.assertTrue(shortn[1] == '...2')
        self.assertTrue(shortn[2] == '...backup')
